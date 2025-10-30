from __future__ import annotations

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...core.config import Settings, get_settings
from ...core.database import get_db
from ...core.errors import ResourceNotFoundError, ValidationError
from ...models.enums import MediaAssetType, ProcessingJobStatus, ProcessingJobType
from ...repositories.media_asset import MediaAssetRepository
from ...repositories.project import ProjectRepository
from ...schemas.media_asset import MediaAssetRead, MediaAssetUploadResponse
from ...schemas.pagination import PaginatedResponse
from ...services.storage_service import (
    ChecksumMismatchError,
    StorageQuotaExceeded,
    StorageService,
)
from ...workers.job_manager import ProcessingJobLifecycle

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("/upload", response_model=MediaAssetUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_asset(
    project_id: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    asset_type: Annotated[MediaAssetType, Form()] = MediaAssetType.SOURCE,
    expected_checksum: Annotated[Optional[str], Form()] = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> MediaAssetUploadResponse:
    """
    Upload a media asset (video or other file) to a project.
    
    Creates a MediaAsset record and, for source videos, initiates
    an ingest processing job.
    
    Args:
        project_id: Project to upload asset to
        file: File to upload
        asset_type: Type of asset (source, generated, etc.)
        expected_checksum: Optional SHA256 checksum for validation
        db: Database session
        settings: Application settings
        
    Returns:
        Upload result with asset_id and optional job_id
        
    Raises:
        ResourceNotFoundError: If project is not found
        ValidationError: If file is invalid or checksum mismatches
        HTTPException: If storage quota is exceeded
    """
    project_repo = ProjectRepository(db)
    project = project_repo.get(project_id)
    
    if project is None:
        raise ResourceNotFoundError("Project", project_id)
    
    if file.filename is None:
        raise ValidationError("File must have a filename")
    
    file_size = getattr(file, "size", None)
    if file_size and file_size > settings.max_upload_size:
        raise ValidationError(
            f"File size {file_size} bytes exceeds maximum allowed size "
            f"{settings.max_upload_size} bytes"
        )
    
    await file.seek(0)
    
    asset_repo = MediaAssetRepository(db)
    storage_service = StorageService(settings, asset_repo)
    
    try:
        asset = storage_service.ingest_media_asset(
            project_id=project_id,
            asset_type=asset_type,
            fileobj=file.file,
            filename=file.filename,
            mime_type=file.content_type,
            expected_checksum=expected_checksum,
        )
    except ChecksumMismatchError as exc:
        logger.warning(
            "Checksum mismatch during upload",
            extra={
                "project_id": project_id,
                "filename": file.filename,
                "expected": exc.expected,
                "actual": exc.actual,
            },
        )
        raise ValidationError(f"Checksum validation failed: {exc}") from exc
    except StorageQuotaExceeded as exc:
        logger.warning(
            "Storage quota exceeded",
            extra={
                "project_id": project_id,
                "filename": file.filename,
                "used_bytes": exc.used_bytes,
                "attempted_bytes": exc.attempted_bytes,
            },
        )
        raise ValidationError(f"Storage quota exceeded: {exc}") from exc
    
    logger.info(
        "Asset uploaded",
        extra={
            "asset_id": asset.id,
            "project_id": project_id,
            "filename": file.filename,
            "asset_type": asset_type.value,
            "size_bytes": asset.size_bytes,
        },
    )
    
    job_id: Optional[str] = None
    job_status: Optional[ProcessingJobStatus] = None
    warning: Optional[str] = None
    
    if asset_type == MediaAssetType.SOURCE:
        try:
            job = ProcessingJobLifecycle.enqueue(
                job_type=ProcessingJobType.INGEST,
                payload={
                    "asset_id": asset.id,
                    "project_id": project_id,
                    "file_path": asset.file_path,
                },
                priority=5,
            )
            job_id = job.id
            job_status = job.status
            
            logger.info(
                "Ingest job enqueued",
                extra={"asset_id": asset.id, "job_id": job.id},
            )
        except RuntimeError as exc:
            logger.error(
                "Failed to enqueue ingest job",
                extra={"asset_id": asset.id, "error": str(exc)},
                exc_info=True,
            )
            warning = "Asset uploaded but background processing could not be started"
    
    return MediaAssetUploadResponse(
        asset_id=asset.id,
        project_id=project_id,
        filename=asset.filename,
        size_bytes=asset.size_bytes,
        checksum=asset.checksum,
        job_id=job_id,
        job_status=job_status,
        warning=warning,
    )


@router.get("/", response_model=PaginatedResponse[MediaAssetRead])
async def list_assets(
    project_id: Annotated[Optional[str], Query()] = None,
    asset_type: Annotated[Optional[MediaAssetType], Query()] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    db: Session = Depends(get_db),
) -> PaginatedResponse[MediaAssetRead]:
    """
    List media assets with optional filtering.
    
    Args:
        project_id: Filter by project ID
        asset_type: Filter by asset type
        offset: Number of assets to skip
        limit: Maximum number of assets to return (1-100)
        db: Database session
        
    Returns:
        Paginated list of media assets
    """
    from ...models.media_asset import MediaAsset
    
    conditions = []
    if project_id:
        conditions.append(MediaAsset.project_id == project_id)
    if asset_type:
        conditions.append(MediaAsset.type == asset_type)
    
    total_stmt = select(func.count()).select_from(MediaAsset)
    if conditions:
        total_stmt = total_stmt.where(*conditions)
    total = db.execute(total_stmt).scalar() or 0
    
    stmt = select(MediaAsset)
    if conditions:
        stmt = stmt.where(*conditions)
    stmt = stmt.order_by(MediaAsset.created_at.desc()).offset(offset).limit(limit)
    
    result = db.execute(stmt)
    assets = result.scalars().all()
    
    return PaginatedResponse[MediaAssetRead](
        items=[MediaAssetRead.model_validate(asset) for asset in assets],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{asset_id}", response_model=MediaAssetRead)
async def get_asset(
    asset_id: str,
    db: Session = Depends(get_db),
) -> MediaAssetRead:
    """
    Get a specific media asset by ID.
    
    Args:
        asset_id: Asset identifier
        db: Database session
        
    Returns:
        Asset details
        
    Raises:
        ResourceNotFoundError: If asset is not found
    """
    repository = MediaAssetRepository(db)
    asset = repository.get(asset_id)
    
    if asset is None:
        raise ResourceNotFoundError("MediaAsset", asset_id)
    
    return MediaAssetRead.model_validate(asset)


__all__ = ["router"]
