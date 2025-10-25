from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, constr


ALLOWED_VIDEO_FORMATS = ["video/mp4", "video/quicktime", "video/x-msvideo", "video/x-matroska", "video/webm"]
ALLOWED_MIME_TYPES = ALLOWED_VIDEO_FORMATS


class VideoAssetBase(BaseModel):
    filename: constr(min_length=1, max_length=255) = Field(..., description="Original filename")
    file_path: constr(min_length=1, max_length=512) = Field(..., description="File storage path")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    mime_type: constr(min_length=1, max_length=100) = Field(..., description="MIME type of the video file")
    duration: Optional[float] = Field(None, ge=0, description="Video duration in seconds")
    width: Optional[int] = Field(None, gt=0, description="Video width in pixels")
    height: Optional[int] = Field(None, gt=0, description="Video height in pixels")
    fps: Optional[float] = Field(None, gt=0, description="Frames per second")
    codec: Optional[str] = Field(None, max_length=50, description="Video codec")


class VideoAssetCreate(VideoAssetBase):
    project_id: int = Field(..., description="Associated project ID")


class VideoAssetUpdate(BaseModel):
    filename: Optional[constr(min_length=1, max_length=255)] = None
    duration: Optional[float] = Field(None, ge=0)
    width: Optional[int] = Field(None, gt=0)
    height: Optional[int] = Field(None, gt=0)
    fps: Optional[float] = Field(None, gt=0)
    codec: Optional[str] = Field(None, max_length=50)


class VideoAssetResponse(VideoAssetBase):
    id: int
    project_id: int
    uploaded_at: datetime

    class Config:
        from_attributes = True
