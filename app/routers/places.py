from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..deps import get_db
from ..models import Project, ProjectPlace
from ..schemas import PlaceCreate, PlaceUpdate, PlaceOut, MAX_PLACES_PER_PROJECT
from ..services.artic_client import artic_client
from ..services.projects import recompute_project_status

router = APIRouter(prefix="/projects/{project_id}/places", tags=["places"])


@router.get("", response_model=list[PlaceOut])
def list_places(
    project_id: int,
    db: Session = Depends(get_db),
    visited: bool | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")

    stmt = select(ProjectPlace).where(ProjectPlace.project_id == project_id)
    if visited is not None:
        stmt = stmt.where(ProjectPlace.visited.is_(visited))

    stmt = stmt.order_by(ProjectPlace.id.asc()).limit(limit).offset(offset)
    return db.scalars(stmt).all()


@router.get("/{place_id}", response_model=PlaceOut)
def get_place(project_id: int, place_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")

    place = db.get(ProjectPlace, place_id)
    if not place or place.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="place not found")
    return place


@router.post("", response_model=PlaceOut, status_code=status.HTTP_201_CREATED)
def add_place(project_id: int, payload: PlaceCreate, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")

    total = db.scalar(select(func.count(ProjectPlace.id)).where(ProjectPlace.project_id == project_id)) or 0
    if total >= MAX_PLACES_PER_PROJECT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"project already has maximum {MAX_PLACES_PER_PROJECT} places",
        )

    existing = db.scalar(
        select(ProjectPlace.id).where(ProjectPlace.project_id == project_id, ProjectPlace.external_id == payload.external_id)
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="place with this external_id already in project")

    artwork = artic_client.get_artwork(payload.external_id)
    if artwork is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"external_id {payload.external_id} not found in ArtIC API (or temporarily unavailable)",
        )

    place = ProjectPlace(
        project_id=project_id,
        external_id=payload.external_id,
        title=artwork.title,
        notes=payload.notes,
        visited=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(place)
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(place)
    return place


@router.patch("/{place_id}", response_model=PlaceOut)
def update_place(project_id: int, place_id: int, payload: PlaceUpdate, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")

    place = db.get(ProjectPlace, place_id)
    if not place or place.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="place not found")

    if payload.notes is not None:
        place.notes = payload.notes

    if payload.visited is not None:
        if payload.visited and not place.visited:
            place.visited = True
            place.visited_at = datetime.utcnow()
        elif not payload.visited and place.visited:
            place.visited = False
            place.visited_at = None

    place.updated_at = datetime.utcnow()
    project.updated_at = datetime.utcnow()

    recompute_project_status(db, project_id)

    db.commit()
    db.refresh(place)
    return place