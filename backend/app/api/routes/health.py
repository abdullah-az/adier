from __future__ import annotations

from fastapi import APIRouter

from ...core.config import get_settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", summary="Service health check")
async def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }
