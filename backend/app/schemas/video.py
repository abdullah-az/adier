from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class VideoAssetBase(BaseModel):
    """Base schema for video assets."""

    filename: str
    original_filename: str
    project_id: str


class VideoAssetCreate(VideoAssetBase):
    """Schema for creating a video asset."""

    relative_path: str
    checksum: str
    size_bytes: int
    mime_type: str


class VideoAssetResponse(VideoAssetBase):
    """Schema for video asset responses."""

    id: str
    relative_path: str
    checksum: str
    size_bytes: int
    mime_type: str
    status: str
    thumbnail_path: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VideoUploadResponse(BaseModel):
    """Response after successful video upload."""

    asset_id: str
    filename: str
    original_filename: str
    size_bytes: int
    project_id: str
    status: str
    message: str = "Upload successful"


class StorageStatsResponse(BaseModel):
    """Storage usage statistics."""

    root: Optional[str] = None
    project_id: Optional[str] = None
    categories: dict[str, dict[str, Any]]
