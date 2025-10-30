from __future__ import annotations

from fastapi import APIRouter

from .routes import (
    assets_router,
    clips_router,
    health_router,
    jobs_router,
    presets_router,
    projects_router,
)

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(jobs_router)
api_router.include_router(projects_router)
api_router.include_router(assets_router)
api_router.include_router(clips_router)
api_router.include_router(presets_router)

__all__ = ["api_router"]
