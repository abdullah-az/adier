"""API route registrations."""

from .health import router as health_router
from .jobs import router as jobs_router

__all__ = ["health_router", "jobs_router"]
