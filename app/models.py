from datetime import date, datetime
from sqlalchemy import (
    String,
    Text,
    Date,
    DateTime,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")  # active|completed
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    places: Mapped[list["ProjectPlace"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectPlace.id",
    )


class ProjectPlace(Base):
    __tablename__ = "project_places"
    __table_args__ = (
        UniqueConstraint("project_id", "external_id", name="uq_project_external_place"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    external_id: Mapped[int] = mapped_column(nullable=False)  # ArtIC artwork id
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    visited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    visited_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="places")
