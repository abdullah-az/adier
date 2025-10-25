from datetime import datetime

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_settings
from app.core.config import Settings
from app.schemas.health import HealthResponse, ProjectInfoResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )


@router.get("/info", response_model=ProjectInfoResponse)
async def project_info(settings: Settings = Depends(get_current_settings)):
    return ProjectInfoResponse(
        name=settings.app_name,
        version=settings.app_version,
        debug=settings.debug
    )
