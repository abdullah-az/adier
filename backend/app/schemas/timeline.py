from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.timeline import MusicPlacement


class SubtitleSegmentPayload(BaseModel):
    id: str = Field(..., description="Unique identifier for the subtitle segment")
    start: float = Field(..., ge=0.0, description="Segment start time in seconds")
    end: float = Field(..., gt=0.0, description="Segment end time in seconds")
    text: str = Field(default="", description="Subtitle text content")
    language: str = Field(default="en", description="Language code (BCP-47)")
    is_visible: bool = Field(default=True, description="Segment visibility toggle")


class SubtitleListResponse(BaseModel):
    segments: List[SubtitleSegmentPayload]
    updated_at: datetime


class SubtitleUpdateRequest(BaseModel):
    segments: List[SubtitleSegmentPayload] = Field(default_factory=list)


class MusicTrackResponse(BaseModel):
    track_id: str
    filename: str
    display_name: str
    relative_path: str
    size_bytes: int
    duration: Optional[float] = None


class MusicTrackListResponse(BaseModel):
    tracks: List[MusicTrackResponse]


class MusicSettingsPayload(BaseModel):
    track_id: Optional[str] = Field(default=None, description="Selected track filename")
    volume: float = Field(default=0.35, ge=0.0, le=1.0)
    fade_in: float = Field(default=1.0, ge=0.0)
    fade_out: float = Field(default=1.0, ge=0.0)
    offset: float = Field(default=0.0, ge=0.0)
    placement: MusicPlacement = Field(default=MusicPlacement.FULL_TIMELINE)
    clip_id: Optional[str] = Field(default=None)
    loop: bool = Field(default=True)
    is_enabled: bool = Field(default=True)


class MusicSettingsResponse(MusicSettingsPayload):
    updated_at: datetime


class TimelineSettingsResponse(BaseModel):
    subtitles: List[SubtitleSegmentPayload]
    music: MusicSettingsPayload
    updated_at: datetime
