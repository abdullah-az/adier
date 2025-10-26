from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TimelineClipBase(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    track_index: int = Field(default=0, ge=0)
    sequence_order: int = Field(default=0, ge=0)
    start_time: float = Field(..., ge=0)
    end_time: float = Field(..., gt=0)
    clip_start: float = Field(..., ge=0)
    clip_end: float = Field(..., gt=0)
    speed: float = Field(default=1.0, gt=0, le=10)
    is_locked: bool = Field(default=False)
    transition_in: Optional[str] = Field(default=None, max_length=64)
    transition_out: Optional[str] = Field(default=None, max_length=64)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_timing(self) -> "TimelineClipBase":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be greater than start_time")
        if self.clip_end <= self.clip_start:
            raise ValueError("clip_end must be greater than clip_start")
        return self


class TimelineClipCreate(TimelineClipBase):
    project_id: str = Field(..., min_length=1)
    video_asset_id: Optional[str] = Field(default=None, min_length=1)


class TimelineClipUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    track_index: Optional[int] = Field(default=None, ge=0)
    sequence_order: Optional[int] = Field(default=None, ge=0)
    start_time: Optional[float] = Field(default=None, ge=0)
    end_time: Optional[float] = Field(default=None, gt=0)
    clip_start: Optional[float] = Field(default=None, ge=0)
    clip_end: Optional[float] = Field(default=None, gt=0)
    speed: Optional[float] = Field(default=None, gt=0, le=10)
    is_locked: Optional[bool] = None
    transition_in: Optional[str] = Field(default=None, max_length=64)
    transition_out: Optional[str] = Field(default=None, max_length=64)
    metadata: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def _check_timing(self) -> "TimelineClipUpdate":
        if self.start_time is not None and self.end_time is not None:
            if self.end_time <= self.start_time:
                raise ValueError("end_time must be greater than start_time")
        if self.clip_start is not None and self.clip_end is not None:
            if self.clip_end <= self.clip_start:
                raise ValueError("clip_end must be greater than clip_start")
        return self


class TimelineClipRead(TimelineClipBase):
    id: str
    project_id: str
    video_asset_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
