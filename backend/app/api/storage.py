from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_storage_service
from app.schemas.video import StorageStatsResponse
from app.services.storage_service import StorageService

router = APIRouter(prefix="/storage", tags=["storage"])


@router.get("/stats", response_model=StorageStatsResponse)
async def global_storage_stats(
    storage_service: StorageService = Depends(get_storage_service),
) -> StorageStatsResponse:
    """Get global storage usage statistics across all projects."""
    stats = storage_service.get_storage_stats()
    return StorageStatsResponse(**stats)
