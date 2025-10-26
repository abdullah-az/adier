from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class SubtitleSegment(BaseModel):
    """Represents a single editable subtitle segment within a timeline."""

    id: str = Field(..., description="Unique identifier for the segment")
    start: float = Field(..., ge=0.0, description="Segment start time in seconds")
    end: float = Field(..., gt=0.0, description="Segment end time in seconds")
    text: str = Field(default="", description="Displayed subtitle text")
    language: str = Field(default="en", description="BCP-47 language tag for the segment")
    is_visible: bool = Field(default=True, description="Whether the segment should be displayed")

    @model_validator(mode="after")
    def _validate_timecodes(self) -> "SubtitleSegment":
        if self.end <= self.start:
            raise ValueError("Subtitle segment end time must be greater than start time")
        return self


class MusicPlacement(str, Enum):
    FULL_TIMELINE = "full_timeline"
    CLIP_SPECIFIC = "clip_specific"


class TimelineMusicSettings(BaseModel):
    track_id: Optional[str] = Field(default=None, description="Filename of the selected track in project music library")
    volume: float = Field(default=0.35, ge=0.0, le=1.0, description="Linear volume multiplier for the music track")
    fade_in: float = Field(default=1.0, ge=0.0, description="Fade-in duration in seconds")
    fade_out: float = Field(default=1.0, ge=0.0, description="Fade-out duration in seconds")
    offset: float = Field(default=0.0, ge=0.0, description="Offset in seconds before the music starts")
    placement: MusicPlacement = Field(default=MusicPlacement.FULL_TIMELINE)
    clip_id: Optional[str] = Field(default=None, description="Optional clip identifier when placement is clip specific")
    loop: bool = Field(default=True, description="Loop the track to cover the entire placement range")
    is_enabled: bool = Field(default=True, description="Allows toggling music on/off without losing configuration")

    @model_validator(mode="after")
    def _validate_clip_context(self) -> "TimelineMusicSettings":
        if self.placement == MusicPlacement.CLIP_SPECIFIC and not self.clip_id:
            raise ValueError("clip_id must be provided when placement is clip_specific")
        return self


class MusicTrack(BaseModel):
    track_id: str = Field(..., description="Unique identifier for the track (filename)")
    filename: str = Field(..., description="Original filename of the music track")
    display_name: str = Field(..., description="Human friendly label for the track")
    relative_path: str = Field(..., description="Storage relative path for media access")
    size_bytes: int = Field(default=0, ge=0, description="File size in bytes")
    duration: Optional[float] = Field(default=None, ge=0.0, description="Optional duration metadata in seconds")


class TimelineSettings(BaseModel):
    project_id: str = Field(..., description="Project identifier the settings are scoped to")
    subtitles: list[SubtitleSegment] = Field(default_factory=list)
    music: TimelineMusicSettings = Field(default_factory=TimelineMusicSettings)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def ordered_subtitles(self) -> list[SubtitleSegment]:
        return sorted(self.subtitles, key=lambda segment: segment.start)


__all__ = [
    "SubtitleSegment",
    "MusicPlacement",
    "TimelineMusicSettings",
    "MusicTrack",
    "TimelineSettings",
]
