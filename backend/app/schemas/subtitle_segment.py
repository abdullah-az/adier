from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, constr

from app.models.enums import SubtitleFormat


class SubtitleSegmentBase(BaseModel):
    project_id: int = Field(..., description="Associated project ID")
    video_asset_id: Optional[int] = Field(None, description="Associated video asset ID")
    timeline_clip_id: Optional[int] = Field(None, description="Associated timeline clip ID")
    language: str = Field(default="en", max_length=10, description="Language code (e.g., 'en', 'es')")
    format: SubtitleFormat = Field(default=SubtitleFormat.SRT, description="Subtitle format")
    start_time: float = Field(..., ge=0, description="Subtitle start time in seconds")
    end_time: float = Field(..., gt=0, description="Subtitle end time in seconds")
    text: constr(min_length=1) = Field(..., description="Subtitle text content")
    speaker: Optional[str] = Field(None, max_length=100, description="Speaker name or identifier")


class SubtitleSegmentCreate(SubtitleSegmentBase):
    pass


class SubtitleSegmentUpdate(BaseModel):
    language: Optional[str] = Field(None, max_length=10)
    format: Optional[SubtitleFormat] = None
    start_time: Optional[float] = Field(None, ge=0)
    end_time: Optional[float] = Field(None, gt=0)
    text: Optional[constr(min_length=1)] = None
    speaker: Optional[str] = Field(None, max_length=100)


class SubtitleSegmentResponse(SubtitleSegmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
