from __future__ import annotations

from fastapi import APIRouter

from .routes import health_router, jobs_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(jobs_router)

__all__ = ["api_router"]
