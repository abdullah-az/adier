from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AudioTrackBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    start_time: float = Field(..., ge=0)
    end_time: float = Field(..., gt=0)
    fade_in: float = Field(default=0.0, ge=0)
    fade_out: float = Field(default=0.0, ge=0)
    volume: float = Field(default=1.0, ge=0, le=2)
    pan: float = Field(default=0.0, ge=-1, le=1)
    is_muted: bool = Field(default=False)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_timing(self) -> "AudioTrackBase":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be greater than start_time")
        return self


class AudioTrackCreate(AudioTrackBase):
    project_id: str = Field(..., min_length=1)
    video_asset_id: Optional[str] = Field(default=None, min_length=1)
    timeline_clip_id: Optional[str] = Field(default=None, min_length=1)


class AudioTrackUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    start_time: Optional[float] = Field(default=None, ge=0)
    end_time: Optional[float] = Field(default=None, gt=0)
    fade_in: Optional[float] = Field(default=None, ge=0)
    fade_out: Optional[float] = Field(default=None, ge=0)
    volume: Optional[float] = Field(default=None, ge=0, le=2)
    pan: Optional[float] = Field(default=None, ge=-1, le=1)
    is_muted: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    video_asset_id: Optional[str] = Field(default=None, min_length=1)
    timeline_clip_id: Optional[str] = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _check_timing(self) -> "AudioTrackUpdate":
        if self.start_time is not None and self.end_time is not None:
            if self.end_time <= self.start_time:
                raise ValueError("end_time must be greater than start_time")
        return self


class AudioTrackRead(AudioTrackBase):
    id: str
    project_id: str
    video_asset_id: Optional[str]
    timeline_clip_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
