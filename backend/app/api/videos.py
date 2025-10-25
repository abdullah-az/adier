from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from loguru import logger

from app.api.dependencies import get_storage_service
from app.models.video_asset import VideoAsset
from app.schemas.video import (
    StorageStatsResponse,
    VideoAssetResponse,
    VideoUploadResponse,
)
from app.services.storage_service import StorageService

router = APIRouter(prefix="/projects/{project_id}", tags=["videos"])


def _to_response(asset: VideoAsset) -> VideoAssetResponse:
    return VideoAssetResponse.model_validate(asset.model_dump())


@router.post("/videos", response_model=VideoUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    project_id: str,
    file: UploadFile = File(..., description="Video file to upload (MP4, MOV, AVI)"),
    storage_service: StorageService = Depends(get_storage_service),
) -> VideoUploadResponse:
    """Upload a video for the specified project and store it on disk."""
    if not file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file uploaded")

    try:
        asset = await storage_service.upload_video(project_id, file)
    except ValueError as exc:
        logger.warning("Video upload rejected", error=str(exc))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - unexpected errors
        logger.exception("Video upload failed", error=str(exc))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Upload failed") from exc

    return VideoUploadResponse(
        asset_id=asset.id,
        filename=asset.filename,
        original_filename=asset.original_filename,
        size_bytes=asset.size_bytes,
        project_id=asset.project_id,
        status=asset.status,
    )


@router.get("/videos", response_model=List[VideoAssetResponse])
async def list_videos(
    project_id: str,
    storage_service: StorageService = Depends(get_storage_service),
) -> List[VideoAssetResponse]:
    """List all video assets for a project."""
    assets = await storage_service.list_project_videos(project_id)
    return [_to_response(asset) for asset in assets]


@router.get("/videos/{asset_id}/thumbnail")
async def get_video_thumbnail(
    project_id: str,
    asset_id: str,
    storage_service: StorageService = Depends(get_storage_service),
) -> FileResponse:
    """Return the thumbnail associated with a specific video asset."""
    asset = await storage_service.get_video_asset(asset_id)
    if not asset or asset.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    thumbnail_path = asset.thumbnail_path
    if not thumbnail_path or thumbnail_path.endswith(".placeholder"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thumbnail not available")

    file_path = storage_service.storage_manager.storage_root / thumbnail_path
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thumbnail file missing")

    return FileResponse(file_path)


@router.delete("/videos/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    project_id: str,
    asset_id: str,
    storage_service: StorageService = Depends(get_storage_service),
) -> None:
    """Delete a video asset and its stored files."""
    asset = await storage_service.get_video_asset(asset_id)
    if not asset or asset.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    await storage_service.delete_video_asset(asset_id)


@router.delete("/storage", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_storage(
    project_id: str,
    storage_service: StorageService = Depends(get_storage_service),
) -> None:
    """Remove all stored files and metadata for a project."""
    await storage_service.delete_project_storage(project_id)


@router.get("/storage/stats", response_model=StorageStatsResponse)
async def project_storage_stats(
    project_id: str,
    storage_service: StorageService = Depends(get_storage_service),
) -> StorageStatsResponse:
    """Get storage usage statistics for a specific project."""
    stats = storage_service.get_storage_stats(project_id)
    return StorageStatsResponse(**stats)
