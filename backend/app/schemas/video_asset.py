from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.models import VideoAssetStatus, VideoAssetType


class VideoAssetBase(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    original_filename: str = Field(..., min_length=1, max_length=255)
    relative_path: str = Field(..., min_length=1, max_length=512)
    mime_type: str = Field(..., min_length=1, max_length=128)
    checksum: str = Field(..., min_length=32, max_length=128)
    file_size: int = Field(..., ge=0)
    duration_seconds: float = Field(..., ge=0)
    frame_rate: float = Field(..., gt=0, le=240)
    resolution_width: int = Field(..., ge=1, le=8192)
    resolution_height: int = Field(..., ge=1, le=8192)
    asset_type: VideoAssetType = Field(default=VideoAssetType.SOURCE)
    status: VideoAssetStatus = Field(default=VideoAssetStatus.UPLOADED)
    waveform_path: Optional[str] = Field(default=None, max_length=512)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("checksum")
    @classmethod
    def _normalise_checksum(cls, value: str) -> str:
        checksum = value.strip().lower()
        if not checksum:
            raise ValueError("checksum cannot be empty")
        return checksum


class VideoAssetCreate(VideoAssetBase):
    project_id: str = Field(..., min_length=1)


class VideoAssetUpdate(BaseModel):
    filename: Optional[str] = Field(default=None, min_length=1, max_length=255)
    original_filename: Optional[str] = Field(default=None, min_length=1, max_length=255)
    relative_path: Optional[str] = Field(default=None, min_length=1, max_length=512)
    mime_type: Optional[str] = Field(default=None, min_length=1, max_length=128)
    checksum: Optional[str] = Field(default=None, min_length=32, max_length=128)
    file_size: Optional[int] = Field(default=None, ge=0)
    duration_seconds: Optional[float] = Field(default=None, ge=0)
    frame_rate: Optional[float] = Field(default=None, gt=0, le=240)
    resolution_width: Optional[int] = Field(default=None, ge=1, le=8192)
    resolution_height: Optional[int] = Field(default=None, ge=1, le=8192)
    asset_type: Optional[VideoAssetType] = None
    status: Optional[VideoAssetStatus] = None
    waveform_path: Optional[str] = Field(default=None, max_length=512)
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("checksum")
    @classmethod
    def _normalise_checksum(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        checksum = value.strip().lower()
        if not checksum:
            raise ValueError("checksum cannot be empty")
        return checksum


class VideoAssetRead(VideoAssetBase):
    id: str
    project_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
