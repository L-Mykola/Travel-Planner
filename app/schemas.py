from __future__ import annotations

from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict

MAX_PLACES_PER_PROJECT = 10
MIN_PLACES_PER_PROJECT = 1


class PlaceCreate(BaseModel):
    external_id: int = Field(..., gt=0)
    notes: str | None = None


class PlaceUpdate(BaseModel):
    notes: str | None = None
    visited: bool | None = None


class PlaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    external_id: int
    title: str | None
    notes: str | None
    visited: bool
    visited_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    start_date: date | None = None
    places: list[PlaceCreate] | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    start_date: date | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    start_date: date | None
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    places_count: int
    visited_count: int


class ProjectWithPlacesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    start_date: date | None
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    places: list[PlaceOut]
