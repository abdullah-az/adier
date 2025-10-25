from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile, status
from loguru import logger

from app.api.dependencies import get_storage_service
from app.models.video_asset import VideoAsset
from app.schemas.common import ApiResponse
from app.schemas.video import (
    StorageStatsResponse,
    VideoAssetResponse,
    VideoUploadResponse,
)
from app.services.storage_service import StorageService
from app.utils.responses import empty_response, error_response, success_response

router = APIRouter(prefix="/projects/{project_id}", tags=["videos"])


def _to_response(asset: VideoAsset) -> VideoAssetResponse:
    return VideoAssetResponse.model_validate(asset.model_dump())


@router.post(
    "/videos",
    response_model=ApiResponse[VideoUploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload a video asset",
)
async def upload_video(
    project_id: str,
    file: UploadFile = File(..., description="Video file to upload (MP4, MOV, AVI)"),
    storage_service: StorageService = Depends(get_storage_service),
) -> ApiResponse[VideoUploadResponse]:
    """Upload a video for the specified project and store it on disk."""
    if not file:
        return error_response(status_code=status.HTTP_400_BAD_REQUEST, code="NO_FILE", message="No file uploaded")

    try:
        asset = await storage_service.upload_video(project_id, file)
    except ValueError as exc:
        logger.warning("Video upload rejected", error=str(exc))
        return error_response(status_code=status.HTTP_400_BAD_REQUEST, code="UPLOAD_REJECTED", message=str(exc))
    except Exception as exc:  # pragma: no cover - unexpected errors
        logger.exception("Video upload failed", error=str(exc))
        return error_response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, code="UPLOAD_FAILED", message="Upload failed")

    response = VideoUploadResponse(
        asset_id=asset.id,
        filename=asset.filename,
        original_filename=asset.original_filename,
        size_bytes=asset.size_bytes,
        project_id=asset.project_id,
        status=asset.status,
    )
    return success_response(response, message="Video uploaded", code="VIDEO_UPLOADED")


@router.get(
    "/videos",
    response_model=ApiResponse[list[VideoAssetResponse]],
    summary="List video assets",
)
async def list_videos(
    project_id: str,
    storage_service: StorageService = Depends(get_storage_service),
) -> ApiResponse[list[VideoAssetResponse]]:
    """List all video assets for a project."""
    assets = await storage_service.list_project_videos(project_id)
    payload = [_to_response(asset) for asset in assets]
    return success_response(payload, message="Video assets retrieved")


@router.delete(
    "/videos/{asset_id}",
    response_model=ApiResponse[None],
    summary="Delete a video asset",
)
async def delete_video(
    project_id: str,
    asset_id: str,
    storage_service: StorageService = Depends(get_storage_service),
) -> ApiResponse[None]:
    """Delete a video asset and its stored files."""
    asset = await storage_service.get_video_asset(asset_id)
    if not asset or asset.project_id != project_id:
        return error_response(status_code=status.HTTP_404_NOT_FOUND, code="ASSET_NOT_FOUND", message="Asset not found")

    await storage_service.delete_video_asset(asset_id)
    return empty_response(message="Video asset deleted", code="VIDEO_DELETED")


@router.delete(
    "/storage",
    response_model=ApiResponse[None],
    summary="Delete all project storage",
)
async def delete_project_storage(
    project_id: str,
    storage_service: StorageService = Depends(get_storage_service),
) -> ApiResponse[None]:
    """Remove all stored files and metadata for a project."""
    await storage_service.delete_project_storage(project_id)
    return empty_response(message="Project storage cleared", code="STORAGE_DELETED")


@router.get(
    "/storage/stats",
    response_model=ApiResponse[StorageStatsResponse],
    summary="Project storage statistics",
)
async def project_storage_stats(
    project_id: str,
    storage_service: StorageService = Depends(get_storage_service),
) -> ApiResponse[StorageStatsResponse]:
    """Get storage usage statistics for a specific project."""
    stats = storage_service.get_storage_stats(project_id)
    return success_response(StorageStatsResponse(**stats), message="Storage stats retrieved")
