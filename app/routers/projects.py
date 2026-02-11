from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..deps import get_db
from ..models import Project, ProjectPlace
from ..schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectOut,
    ProjectWithPlacesOut,
    MIN_PLACES_PER_PROJECT,
    MAX_PLACES_PER_PROJECT,
)
from ..services.artic_client import artic_client
from ..services.projects import recompute_project_status, project_counts

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectWithPlacesOut, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    if payload.places is not None:
        if not (MIN_PLACES_PER_PROJECT <= len(payload.places) <= MAX_PLACES_PER_PROJECT):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"places must be between {MIN_PLACES_PER_PROJECT} and {MAX_PLACES_PER_PROJECT}",
            )
        # prevent duplicates inside request array
        seen = set()
        for p in payload.places:
            if p.external_id in seen:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="duplicate external_id in places array")
            seen.add(p.external_id)

    project = Project(
        name=payload.name,
        description=payload.description,
        start_date=payload.start_date,
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(project)
    db.flush()  # get project.id

    if payload.places:
        for p in payload.places:
            artwork = artic_client.get_artwork(p.external_id)
            if artwork is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"external_id {p.external_id} not found in ArtIC API (or temporarily unavailable)",
                )
            db.add(
                ProjectPlace(
                    project_id=project.id,
                    external_id=p.external_id,
                    title=artwork.title,
                    notes=p.notes,
                    visited=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )

    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=list[ProjectOut])
def list_projects(
    db: Session = Depends(get_db),
    status_filter: Literal["active", "completed"] | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    stmt = select(Project)
    if status_filter:
        stmt = stmt.where(Project.status == status_filter)

    stmt = stmt.order_by(Project.id.desc()).limit(limit).offset(offset)
    projects = db.scalars(stmt).all()

    out: list[ProjectOut] = []
    for p in projects:
        total, visited = project_counts(db, p.id)
        out.append(
            ProjectOut(
                id=p.id,
                name=p.name,
                description=p.description,
                start_date=p.start_date,
                status=p.status,
                created_at=p.created_at,
                updated_at=p.updated_at,
                completed_at=p.completed_at,
                places_count=total,
                visited_count=visited,
            )
        )
    return out


@router.get("/{project_id}", response_model=ProjectWithPlacesOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")
    # places relationship loads lazily; but OK for sqlite/simple
    return project


@router.patch("/{project_id}", response_model=ProjectWithPlacesOut)
def update_project(project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")

    if payload.name is not None:
        project.name = payload.name
    if payload.description is not None:
        project.description = payload.description
    if payload.start_date is not None:
        project.start_date = payload.start_date

    project.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")

    visited_count = db.scalar(
        select(func.count(ProjectPlace.id)).where(ProjectPlace.project_id == project_id, ProjectPlace.visited.is_(True))
    ) or 0

    if visited_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="project cannot be deleted because it has visited places",
        )

    db.delete(project)
    db.commit()
    return None
