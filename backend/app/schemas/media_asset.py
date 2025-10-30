from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from ..models.enums import MediaAssetType, ProcessingJobStatus
from .base import TimestampedSchema


class MediaAssetBase(BaseModel):
    project_id: str
    type: MediaAssetType
    filename: str
    file_path: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    duration_seconds: Optional[float] = None
    checksum: Optional[str] = None


class MediaAssetCreate(MediaAssetBase):
    pass


class MediaAssetUpdate(BaseModel):
    type: Optional[MediaAssetType] = None
    filename: Optional[str] = None
    file_path: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    duration_seconds: Optional[float] = None
    checksum: Optional[str] = None


class MediaAssetRead(MediaAssetBase, TimestampedSchema):
    pass


class MediaAssetUploadResponse(BaseModel):
    asset_id: str
    project_id: str
    filename: str
    size_bytes: Optional[int] = None
    checksum: Optional[str] = None
    job_id: Optional[str] = None
    job_status: Optional[ProcessingJobStatus] = None
    warning: Optional[str] = None


__all__ = [
    "MediaAssetBase",
    "MediaAssetCreate",
    "MediaAssetUpdate",
    "MediaAssetRead",
    "MediaAssetUploadResponse",
]
