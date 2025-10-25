from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse

from app.api.dependencies import get_storage_manager, get_storage_service
from app.schemas.common import ApiResponse
from app.schemas.video import VideoAssetResponse
from app.services.storage_service import StorageService
from app.utils.responses import error_response, success_response
from app.utils.storage import StorageManager

router = APIRouter(prefix="/projects/{project_id}/assets", tags=["assets"])


@router.get(
    "/{asset_id}",
    response_model=ApiResponse[VideoAssetResponse],
    summary="Get asset metadata",
)
async def get_asset(
    project_id: str,
    asset_id: str,
    storage_service: StorageService = Depends(get_storage_service),
) -> ApiResponse[VideoAssetResponse]:
    asset = await storage_service.get_video_asset(asset_id)
    if asset is None or asset.project_id != project_id:
        return error_response(status_code=status.HTTP_404_NOT_FOUND, code="ASSET_NOT_FOUND", message="Asset not found")
    return success_response(VideoAssetResponse.model_validate(asset.model_dump()), message="Asset retrieved")


@router.get(
    "/{asset_id}/download",
    response_class=FileResponse,
    summary="Download an asset file",
)
async def download_asset(
    project_id: str,
    asset_id: str,
    storage_service: StorageService = Depends(get_storage_service),
    storage_manager: StorageManager = Depends(get_storage_manager),
):
    asset = await storage_service.get_video_asset(asset_id)
    if asset is None or asset.project_id != project_id:
        return error_response(status_code=status.HTTP_404_NOT_FOUND, code="ASSET_NOT_FOUND", message="Asset not found")
    absolute_path = Path(storage_manager.storage_root) / asset.relative_path
    if not absolute_path.exists():
        return error_response(status_code=status.HTTP_404_NOT_FOUND, code="FILE_NOT_FOUND", message="Asset file missing")
    return FileResponse(
        path=absolute_path,
        media_type=asset.mime_type,
        filename=asset.original_filename or asset.filename,
    )
