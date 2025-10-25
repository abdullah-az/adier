from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import TimelineTrackType


class TimelineClipBase(BaseModel):
    project_id: int = Field(..., description="Associated project ID")
    video_asset_id: Optional[int] = Field(None, description="Associated video asset ID")
    track_number: int = Field(..., ge=0, description="Track number on the timeline")
    track_type: TimelineTrackType = Field(default=TimelineTrackType.VIDEO, description="Type of track")
    start_time: float = Field(..., ge=0, description="Clip start time on timeline")
    end_time: float = Field(..., gt=0, description="Clip end time on timeline")
    source_start: float = Field(..., ge=0, description="Source asset start time")
    source_end: float = Field(..., gt=0, description="Source asset end time")
    volume: float = Field(default=1.0, ge=0, le=2, description="Clip volume multiplier")
    muted: bool = Field(default=False, description="Whether the clip is muted")
    locked: bool = Field(default=False, description="Whether the clip is locked")
    transition_in: Optional[str] = Field(None, max_length=50, description="Transition applied at the start")
    transition_out: Optional[str] = Field(None, max_length=50, description="Transition applied at the end")
    effects: Optional[str] = Field(None, description="Serialized effects configuration")


class TimelineClipCreate(TimelineClipBase):
    pass


class TimelineClipUpdate(BaseModel):
    track_number: Optional[int] = Field(None, ge=0)
    track_type: Optional[TimelineTrackType] = None
    start_time: Optional[float] = Field(None, ge=0)
    end_time: Optional[float] = Field(None, gt=0)
    source_start: Optional[float] = Field(None, ge=0)
    source_end: Optional[float] = Field(None, gt=0)
    volume: Optional[float] = Field(None, ge=0, le=2)
    muted: Optional[bool] = None
    locked: Optional[bool] = None
    transition_in: Optional[str] = Field(None, max_length=50)
    transition_out: Optional[str] = Field(None, max_length=50)
    effects: Optional[str] = None


class TimelineClipResponse(TimelineClipBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
