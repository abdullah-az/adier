from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_storage_service
from app.schemas.common import ApiResponse
from app.schemas.video import StorageStatsResponse
from app.services.storage_service import StorageService
from app.utils.responses import success_response

router = APIRouter(prefix="/storage", tags=["storage"])


@router.get(
    "/stats",
    response_model=ApiResponse[StorageStatsResponse],
    summary="Get global storage statistics",
)
async def global_storage_stats(
    storage_service: StorageService = Depends(get_storage_service),
) -> ApiResponse[StorageStatsResponse]:
    """Get global storage usage statistics across all projects."""
    stats = storage_service.get_storage_stats()
    return success_response(StorageStatsResponse(**stats), message="Storage stats retrieved")
