from __future__ import annotations

import math
from typing import Any, List, Optional, Tuple

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from loguru import logger

from app.api.errors import APIError
from app.api.dependencies import get_storage_service
from app.models.video_asset import VideoAsset
from app.schemas.common import PaginationMeta
from app.schemas.video import (
    StorageStatsResponse,
    VideoAssetCollectionResponse,
    VideoAssetResponse,
    VideoUploadResponse,
)
from app.services.storage_service import StorageService

router = APIRouter(prefix="/projects/{project_id}", tags=["videos"])


def _to_response(asset: VideoAsset) -> VideoAssetResponse:
    return VideoAssetResponse.model_validate(asset.model_dump())


def _parse_sort(value: str) -> Tuple[str, str]:
    if ":" in value:
        field, direction = value.split(":", 1)
    else:
        field, direction = value, "asc"
    field = field.strip().lower()
    direction = direction.strip().lower()
    if field not in {"created_at", "filename", "size"}:
        field = "created_at"
    if direction not in {"asc", "desc"}:
        direction = "asc"
    return field, direction


def _asset_sort_key(asset: VideoAsset, field: str) -> Any:
    if field == "filename":
        return asset.filename.lower()
    if field == "size":
        return asset.size_bytes
    return asset.created_at


@router.post("/videos", response_model=VideoUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    project_id: str,
    file: UploadFile = File(..., description="Video file to upload (MP4, MOV, AVI)"),
    storage_service: StorageService = Depends(get_storage_service),
) -> VideoUploadResponse:
    """Upload a video for the specified project and store it on disk."""
    if not file:
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, code="missing_file", message="No file provided for upload")

    try:
        asset = await storage_service.upload_video(project_id, file)
    except ValueError as exc:
        logger.warning("Video upload rejected", error=str(exc))
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, code="invalid_file", message=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - unexpected errors
        logger.exception("Video upload failed", error=str(exc))
        raise APIError(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, code="upload_failed", message="Video upload failed", details={"reason": str(exc)}) from exc

    return VideoUploadResponse(
        asset_id=asset.id,
        filename=asset.filename,
        original_filename=asset.original_filename,
        size_bytes=asset.size_bytes,
        project_id=asset.project_id,
        status=asset.status,
    )


@router.get("/videos", response_model=VideoAssetCollectionResponse)
async def list_videos(
    project_id: str,
    storage_service: StorageService = Depends(get_storage_service),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    sort: str = Query("created_at:desc", description="Sort expression e.g. created_at:desc"),
    locale: Optional[str] = Query(None, description="Optional locale metadata for clients"),
) -> VideoAssetCollectionResponse:
    """List stored video assets for a project with pagination support."""
    assets = await storage_service.list_project_videos(project_id)
    field, direction = _parse_sort(sort)
    assets.sort(key=lambda asset: _asset_sort_key(asset, field), reverse=(direction == "desc"))

    total = len(assets)
    start = max((page - 1) * page_size, 0)
    end = start + page_size
    items = [_to_response(asset) for asset in assets[start:end]]
    total_pages = math.ceil(total / page_size) if total else 0
    pagination = PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        sort=sort,
        locale=locale,
    )
    return VideoAssetCollectionResponse(items=items, pagination=pagination)


@router.delete("/videos/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    project_id: str,
    asset_id: str,
    storage_service: StorageService = Depends(get_storage_service),
) -> None:
    """Delete a video asset and its stored files."""
    asset = await storage_service.get_video_asset(asset_id)
    if not asset or asset.project_id != project_id:
        raise APIError(status_code=status.HTTP_404_NOT_FOUND, code="asset_not_found", message="Asset not found")

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
