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
    TransitionSpec,
    WatermarkSpec,
)
from app.models.timeline import SubtitleSegment, SubtitleTrack, Timeline, TimelineSegment


class TimelineSegmentPayload(BaseModel):
    """Payload describing a timeline segment."""

    id: Optional[str] = Field(default=None)
    asset_id: str
    timeline_start: float = Field(..., ge=0.0)
    in_point: float = Field(default=0.0, ge=0.0)
    out_point: float = Field(..., gt=0.0)
    include_audio: bool = Field(default=True)
    transition: TransitionSpec = Field(default_factory=TransitionSpec)
    notes: Optional[str] = Field(default=None, max_length=500)

    def to_model(self) -> TimelineSegment:
        payload = self.model_dump()
        identifier = payload.pop("id") or None
        if identifier is not None:
            payload["id"] = identifier
        else:
            payload.pop("id", None)
        return TimelineSegment(**payload)

    @classmethod
    def from_model(cls, segment: TimelineSegment) -> "TimelineSegmentPayload":
        return cls.model_validate(segment.model_dump())


class SubtitleSegmentPayload(BaseModel):
    id: Optional[str] = Field(default=None)
    start: float = Field(..., ge=0.0)
    end: float = Field(..., gt=0.0)
    text: str = Field(..., max_length=1000)
    speaker: Optional[str] = Field(default=None, max_length=120)

    def to_model(self) -> SubtitleSegment:
        payload = self.model_dump()
        identifier = payload.pop("id") or None
        if identifier is not None:
            payload["id"] = identifier
        else:
            payload.pop("id", None)
        return SubtitleSegment(**payload)

    @classmethod
    def from_model(cls, segment: SubtitleSegment) -> "SubtitleSegmentPayload":
        return cls.model_validate(segment.model_dump())


class SubtitleTrackPayload(BaseModel):
    id: Optional[str] = Field(default=None)
    locale: str = Field(default="en")
    title: Optional[str] = Field(default=None, max_length=200)
    segments: list[SubtitleSegmentPayload] = Field(default_factory=list)

    def to_model(self) -> SubtitleTrack:
        payload = self.model_dump()
        segments = payload.pop("segments")
        identifier = payload.pop("id") or None
        track = SubtitleTrack(**payload)
        if identifier is not None:
            track.id = identifier
        track.segments = [segment.to_model() for segment in segments]
        return track

    @classmethod
    def from_model(cls, track: SubtitleTrack) -> "SubtitleTrackPayload":
        return cls(
            id=track.id,
            locale=track.locale,
            title=track.title,
            segments=[SubtitleSegmentPayload.from_model(segment) for segment in track.segments],
        )


class TimelineCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    locale: Optional[str] = Field(default=None)
    segments: list[TimelineSegmentPayload] = Field(default_factory=list)
    aspect_ratio: Optional[AspectRatio] = Field(default=None)
    resolution: Optional[ResolutionPreset] = Field(default=None)
    proxy_resolution: Optional[ResolutionPreset] = Field(default=None)
    generate_thumbnails: Optional[bool] = Field(default=None)
    background_music: Optional[BackgroundMusicSpec] = Field(default=None)
    export_templates: list[ExportTemplate] = Field(default_factory=list)
    default_watermark: Optional[WatermarkSpec] = Field(default=None)


class TimelineUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    locale: Optional[str] = Field(default=None)
    segments: Optional[list[TimelineSegmentPayload]] = Field(default=None)
    aspect_ratio: Optional[AspectRatio] = Field(default=None)
    resolution: Optional[ResolutionPreset] = Field(default=None)
    proxy_resolution: Optional[ResolutionPreset] = Field(default=None)
    generate_thumbnails: Optional[bool] = Field(default=None)


class BackgroundMusicUpdateRequest(BaseModel):
    background_music: Optional[BackgroundMusicSpec] = Field(default=None)


class SubtitleTrackUpsertRequest(BaseModel):
    track: SubtitleTrackPayload


class ExportTemplateUpdateRequest(BaseModel):
    templates: list[ExportTemplate] = Field(default_factory=list)


class WatermarkUpdateRequest(BaseModel):
    watermark: Optional[WatermarkSpec] = Field(default=None)


class TimelineSegmentResponse(BaseModel):
    id: str
    asset_id: str
    timeline_start: float
    in_point: float
    out_point: float
    include_audio: bool
    transition: TransitionSpec
    notes: Optional[str] = None

    @classmethod
    def from_model(cls, segment: TimelineSegment) -> "TimelineSegmentResponse":
        return cls.model_validate(segment.model_dump())


class SubtitleSegmentResponse(BaseModel):
    id: str
    start: float
    end: float
    text: str
    speaker: Optional[str] = None

    @classmethod
    def from_model(cls, segment: SubtitleSegment) -> "SubtitleSegmentResponse":
        return cls.model_validate(segment.model_dump())


class SubtitleTrackResponse(BaseModel):
    id: str
    locale: str
    title: Optional[str] = None
    segments: list[SubtitleSegmentResponse] = Field(default_factory=list)

    @classmethod
    def from_model(cls, track: SubtitleTrack) -> "SubtitleTrackResponse":
        return cls(
            id=track.id,
            locale=track.locale,
            title=track.title,
            segments=[SubtitleSegmentResponse.from_model(segment) for segment in track.segments],
        )


class TimelineSummary(BaseModel):
    id: str
    name: str
    description: Optional[str]
    locale: str
    aspect_ratio: AspectRatio
    resolution: ResolutionPreset
    segment_count: int
    created_at: datetime
    updated_at: datetime
    version: int

    @classmethod
    def from_model(cls, timeline: Timeline) -> "TimelineSummary":
        return cls(
            id=timeline.id,
            name=timeline.name,
            description=timeline.description,
            locale=timeline.locale,
            aspect_ratio=timeline.aspect_ratio,
            resolution=timeline.resolution,
            segment_count=len(timeline.segments),
            created_at=timeline.created_at,
            updated_at=timeline.updated_at,
            version=timeline.version,
        )


class TimelineResponse(TimelineSummary):
    segments: list[TimelineSegmentResponse] = Field(default_factory=list)
    subtitle_tracks: list[SubtitleTrackResponse] = Field(default_factory=list)
    background_music: Optional[BackgroundMusicSpec] = None
    default_watermark: Optional[WatermarkSpec] = None
    export_templates: list[ExportTemplate] = Field(default_factory=list)
    proxy_resolution: ResolutionPreset
    generate_thumbnails: bool
    last_preview_job_id: Optional[str] = None
    last_export_job_id: Optional[str] = None

    @classmethod
    def from_model(cls, timeline: Timeline) -> "TimelineResponse":
        summary = TimelineSummary.from_model(timeline)
        return cls(
            **summary.model_dump(),
            segments=[TimelineSegmentResponse.from_model(segment) for segment in timeline.segments],
            subtitle_tracks=[SubtitleTrackResponse.from_model(track) for track in timeline.subtitle_tracks],
            background_music=timeline.background_music,
            default_watermark=timeline.default_watermark,
            export_templates=timeline.export_templates,
            proxy_resolution=timeline.proxy_resolution,
            generate_thumbnails=timeline.generate_thumbnails,
            last_preview_job_id=timeline.last_preview_job_id,
            last_export_job_id=timeline.last_export_job_id,
        )


class TimelineJobResponse(BaseModel):
    job_id: str = Field(..., description="Identifier of the enqueued job")
    operation: str = Field(..., description="Operation the job performs")


class TimelineProgressPayload(BaseModel):
    preview: Optional[dict] = None
    export: Optional[dict] = None


class TimelineThumbnailResponse(BaseModel):
    asset_id: str
    segment_id: str
    path: str
    clip_index: Optional[int] = None
    generated_at: Optional[str] = None


__all__ = [
    "TimelineCreateRequest",
    "TimelineUpdateRequest",
    "TimelineResponse",
    "TimelineSummary",
    "TimelineSegmentPayload",
    "TimelineSegmentResponse",
    "SubtitleTrackPayload",
    "SubtitleTrackResponse",
    "BackgroundMusicUpdateRequest",
    "SubtitleTrackUpsertRequest",
    "ExportTemplateUpdateRequest",
    "WatermarkUpdateRequest",
    "TimelineJobResponse",
    "TimelineProgressPayload",
    "TimelineThumbnailResponse",
]
