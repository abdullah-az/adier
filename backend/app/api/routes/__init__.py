"""API route registrations."""

from .assets import router as assets_router
from .clips import router as clips_router
from .health import router as health_router
from .jobs import router as jobs_router
from .presets import router as presets_router
from .progress import router as progress_router
from .projects import router as projects_router

__all__ = [
    "health_router",
    "jobs_router",
    "projects_router",
    "assets_router",
    "clips_router",
    "presets_router",
    "progress_router",
]
