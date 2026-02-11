from __future__ import annotations

from fastapi import FastAPI
from .db import engine, Base
from .routers.projects import router as projects_router
from .routers.places import router as places_router

app = FastAPI(
    title="Travel Projects API",
    version="1.0.0",
    description="Manage travel projects, places (ArtIC artworks), notes, and visited state.",
)

Base.metadata.create_all(bind=engine)

app.include_router(projects_router)
app.include_router(places_router)


@app.get("/health")
def health():
    return {"status": "ok"}
