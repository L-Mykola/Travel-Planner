from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..models import Project, ProjectPlace


MAX_PLACES_PER_PROJECT = 10


def recompute_project_status(db: Session, project_id: int) -> None:
    total = db.scalar(select(func.count(ProjectPlace.id)).where(ProjectPlace.project_id == project_id)) or 0
    visited = db.scalar(
        select(func.count(ProjectPlace.id)).where(ProjectPlace.project_id == project_id, ProjectPlace.visited.is_(True))
    ) or 0

    project = db.get(Project, project_id)
    if not project:
        return

    project.updated_at = datetime.utcnow()

    if total > 0 and total == visited:
        if project.status != "completed":
            project.status = "completed"
            project.completed_at = datetime.utcnow()
    else:
        if project.status != "active":
            project.status = "active"
            project.completed_at = None


def project_counts(db: Session, project_id: int) -> tuple[int, int]:
    total = db.scalar(select(func.count(ProjectPlace.id)).where(ProjectPlace.project_id == project_id)) or 0
    visited = db.scalar(
        select(func.count(ProjectPlace.id)).where(ProjectPlace.project_id == project_id, ProjectPlace.visited.is_(True))
    ) or 0
    return total, visited
