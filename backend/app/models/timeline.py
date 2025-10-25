from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from app.models.pipeline import (
    AspectRatio,
    BackgroundMusicSpec,
    ExportTemplate,
    ResolutionPreset,
    TimelineClip,
    TransitionSpec,
    WatermarkSpec,
)


def _generate_segment_id() -> str:
    return str(uuid4())


class SubtitleSegment(BaseModel):
    """Represents a segment of text for a subtitle track."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    start: float = Field(..., ge=0.0, description="Start timestamp in seconds")
    end: float = Field(..., gt=0.0, description="End timestamp in seconds")
    text: str = Field(..., description="Subtitle text content")
    speaker: Optional[str] = Field(default=None, description="Optional speaker attribution")

    def duration(self) -> float:
        return max(self.end - self.start, 0.0)


class SubtitleTrack(BaseModel):
    """Collection of subtitle segments associated with a locale."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    locale: str = Field(default="en")
    title: Optional[str] = Field(default=None)
    segments: list[SubtitleSegment] = Field(default_factory=list)


class TimelineSegment(BaseModel):
    """Represents a clip placed on a timeline with timeline-relative positioning."""

    id: str = Field(default_factory=_generate_segment_id)
    asset_id: str = Field(..., description="Identifier of the source asset")
    timeline_start: float = Field(..., ge=0.0, description="Start time on the resulting timeline")
    in_point: float = Field(default=0.0, ge=0.0, description="In point on the source asset")
    out_point: float = Field(..., gt=0.0, description="Out point on the source asset")
    include_audio: bool = Field(default=True)
    transition: TransitionSpec = Field(default_factory=TransitionSpec)
    notes: Optional[str] = Field(default=None)

    def duration(self) -> float:
        return max(self.out_point - self.in_point, 0.0)

    @property
    def timeline_end(self) -> float:
        return self.timeline_start + self.duration()

    def to_clip(self) -> TimelineClip:
        return TimelineClip(
            asset_id=self.asset_id,
            in_point=self.in_point,
            out_point=self.out_point,
            include_audio=self.include_audio,
            transition=self.transition,
        )


class Timeline(BaseModel):
    """Domain model describing a timeline configuration composed of segments."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str = Field(...)
    name: str = Field(...)
    description: Optional[str] = Field(default=None)
    locale: str = Field(default="en")
    aspect_ratio: AspectRatio = Field(default=AspectRatio.SIXTEEN_NINE)
    resolution: ResolutionPreset = Field(default=ResolutionPreset.P1080)
    proxy_resolution: ResolutionPreset = Field(default=ResolutionPreset.P720)
    generate_thumbnails: bool = Field(default=True)
    segments: list[TimelineSegment] = Field(default_factory=list)
    subtitle_tracks: list[SubtitleTrack] = Field(default_factory=list)
    background_music: Optional[BackgroundMusicSpec] = Field(default=None)
    default_watermark: Optional[WatermarkSpec] = Field(default=None)
    export_templates: list[ExportTemplate] = Field(default_factory=list)
    last_preview_job_id: Optional[str] = Field(default=None)
    last_export_job_id: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(default=1, ge=1)

    model_config = {"json_encoders": {datetime: lambda value: value.isoformat()}}

    def duration(self) -> float:
        if not self.segments:
            return 0.0
        return max(segment.timeline_end for segment in self.segments)

    def get_subtitle_track(self, locale: Optional[str] = None) -> Optional[SubtitleTrack]:
        if locale:
            for track in self.subtitle_tracks:
                if track.locale.lower() == locale.lower():
                    return track
        return self.subtitle_tracks[0] if self.subtitle_tracks else None


__all__ = [
    "Timeline",
    "TimelineSegment",
    "SubtitleTrack",
    "SubtitleSegment",
]
