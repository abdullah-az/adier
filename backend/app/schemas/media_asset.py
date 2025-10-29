from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from ..models.enums import MediaAssetType
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


__all__ = [
    "MediaAssetBase",
    "MediaAssetCreate",
    "MediaAssetUpdate",
    "MediaAssetRead",
]
