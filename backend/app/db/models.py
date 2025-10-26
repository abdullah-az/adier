from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, generate_uuid


class VideoAssetType(StrEnum):
    SOURCE = "source"
    PROXY = "proxy"
    AUDIO = "audio"
    IMAGE = "image"
    EXPORT = "export"


class VideoAssetStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class ExportFormat(StrEnum):
    MP4 = "mp4"
    MOV = "mov"
    MKV = "mkv"
    GIF = "gif"
    WAV = "wav"


class JobStatusCode(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text())
    frame_rate: Mapped[float] = mapped_column(Float, nullable=False, default=24.0)
    resolution_width: Mapped[int] = mapped_column(Integer, nullable=False, default=1920)
    resolution_height: Mapped[int] = mapped_column(Integer, nullable=False, default=1080)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(512))
    color_profile: Mapped[Optional[str]] = mapped_column(String(64))

    __table_args__ = (
        CheckConstraint("frame_rate > 0", name="frame_rate_positive"),
        CheckConstraint("resolution_width > 0", name="resolution_width_positive"),
        CheckConstraint("resolution_height > 0", name="resolution_height_positive"),
        CheckConstraint("duration_seconds >= 0", name="duration_non_negative"),
    )

    video_assets: Mapped[List["VideoAsset"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    scenes: Mapped[List["SceneDetection"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    subtitles: Mapped[List["SubtitleSegment"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    timeline_clips: Mapped[List["TimelineClip"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    audio_tracks: Mapped[List["AudioTrack"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    export_jobs: Mapped[List["ExportJob"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class VideoAsset(TimestampMixin, Base):
    __tablename__ = "video_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    relative_path: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    frame_rate: Mapped[float] = mapped_column(Float, nullable=False, default=24.0)
    resolution_width: Mapped[int] = mapped_column(Integer, nullable=False, default=1920)
    resolution_height: Mapped[int] = mapped_column(Integer, nullable=False, default=1080)
    waveform_path: Mapped[Optional[str]] = mapped_column(String(512))
    metadata: Mapped[Dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        default=dict,
        nullable=False,
    )
    asset_type: Mapped[VideoAssetType] = mapped_column(
        SAEnum(VideoAssetType, name="video_asset_type", native_enum=False),
        nullable=False,
        default=VideoAssetType.SOURCE,
    )
    status: Mapped[VideoAssetStatus] = mapped_column(
        SAEnum(VideoAssetStatus, name="video_asset_status", native_enum=False),
        nullable=False,
        default=VideoAssetStatus.UPLOADED,
    )

    __table_args__ = (
        CheckConstraint("duration_seconds >= 0", name="duration_non_negative"),
        CheckConstraint("frame_rate > 0", name="frame_rate_positive"),
        CheckConstraint("file_size >= 0", name="file_size_non_negative"),
        CheckConstraint("resolution_width > 0", name="resolution_width_positive"),
        CheckConstraint("resolution_height > 0", name="resolution_height_positive"),
    )

    project: Mapped[Project] = relationship(back_populates="video_assets")
    scenes: Mapped[List["SceneDetection"]] = relationship(
        back_populates="asset",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    subtitles: Mapped[List["SubtitleSegment"]] = relationship(
        back_populates="asset",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    timeline_clips: Mapped[List["TimelineClip"]] = relationship(
        back_populates="asset",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    audio_tracks: Mapped[List["AudioTrack"]] = relationship(
        back_populates="asset",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    export_jobs: Mapped[List["ExportJob"]] = relationship(
        back_populates="output_asset",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class SceneDetection(TimestampMixin, Base):
    __tablename__ = "scene_detections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    video_asset_id: Mapped[str] = mapped_column(
        ForeignKey("video_assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label: Mapped[Optional[str]] = mapped_column(String(255))
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    metadata: Mapped[Dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        default=dict,
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("end_time > start_time", name="valid_scene_duration"),
        CheckConstraint("confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name="confidence_range"),
    )

    project: Mapped[Project] = relationship(back_populates="scenes")
    asset: Mapped[VideoAsset] = relationship(back_populates="scenes")


class SubtitleSegment(TimestampMixin, Base):
    __tablename__ = "subtitle_segments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    video_asset_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("video_assets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    speaker: Mapped[Optional[str]] = mapped_column(String(128))
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    text: Mapped[str] = mapped_column(Text(), nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata: Mapped[Dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        default=dict,
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("end_time > start_time", name="valid_subtitle_duration"),
    )

    project: Mapped[Project] = relationship(back_populates="subtitles")
    asset: Mapped[Optional[VideoAsset]] = relationship(back_populates="subtitles")


class TimelineClip(TimestampMixin, Base):
    __tablename__ = "timeline_clips"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    video_asset_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("video_assets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[Optional[str]] = mapped_column(String(255))
    track_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    clip_start: Mapped[float] = mapped_column(Float, nullable=False)
    clip_end: Mapped[float] = mapped_column(Float, nullable=False)
    speed: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    transition_in: Mapped[Optional[str]] = mapped_column(String(64))
    transition_out: Mapped[Optional[str]] = mapped_column(String(64))
    metadata: Mapped[Dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        default=dict,
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("end_time > start_time", name="valid_clip_duration"),
        CheckConstraint("clip_end > clip_start", name="valid_clip_range"),
        CheckConstraint("speed > 0", name="positive_speed"),
        CheckConstraint("track_index >= 0", name="non_negative_track_index"),
        CheckConstraint("sequence_order >= 0", name="non_negative_sequence_order"),
    )

    project: Mapped[Project] = relationship(back_populates="timeline_clips")
    asset: Mapped[Optional[VideoAsset]] = relationship(back_populates="timeline_clips")
    audio_tracks: Mapped[List["AudioTrack"]] = relationship(
        back_populates="clip",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class AudioTrack(TimestampMixin, Base):
    __tablename__ = "audio_tracks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    video_asset_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("video_assets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    timeline_clip_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("timeline_clips.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    fade_in: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fade_out: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    volume: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    pan: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_muted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata: Mapped[Dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        default=dict,
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("end_time > start_time", name="valid_audio_duration"),
        CheckConstraint("fade_in >= 0", name="non_negative_fade_in"),
        CheckConstraint("fade_out >= 0", name="non_negative_fade_out"),
        CheckConstraint("volume >= 0 AND volume <= 2", name="volume_range"),
        CheckConstraint("pan >= -1 AND pan <= 1", name="pan_range"),
    )

    project: Mapped[Project] = relationship(back_populates="audio_tracks")
    asset: Mapped[Optional[VideoAsset]] = relationship(back_populates="audio_tracks")
    clip: Mapped[Optional[TimelineClip]] = relationship(back_populates="audio_tracks")


class JobStatus(Base):
    __tablename__ = "job_statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[JobStatusCode] = mapped_column(
        SAEnum(JobStatusCode, name="job_status_code", native_enum=False),
        nullable=False,
        unique=True,
    )
    description: Mapped[Optional[str]] = mapped_column(String(255))

    export_jobs: Mapped[List["ExportJob"]] = relationship(back_populates="status")


class ExportJob(TimestampMixin, Base):
    __tablename__ = "export_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    output_asset_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("video_assets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status_id: Mapped[int] = mapped_column(
        ForeignKey("job_statuses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    format: Mapped[ExportFormat] = mapped_column(
        SAEnum(ExportFormat, name="export_format", native_enum=False),
        nullable=False,
    )
    preset: Mapped[Optional[str]] = mapped_column(String(64))
    resolution_width: Mapped[int] = mapped_column(Integer, nullable=False, default=1920)
    resolution_height: Mapped[int] = mapped_column(Integer, nullable=False, default=1080)
    frame_rate: Mapped[float] = mapped_column(Float, nullable=False, default=24.0)
    progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    output_path: Mapped[Optional[str]] = mapped_column(String(512))
    error_message: Mapped[Optional[str]] = mapped_column(Text())
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    metadata: Mapped[Dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        default=dict,
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("resolution_width > 0", name="resolution_width_positive"),
        CheckConstraint("resolution_height > 0", name="resolution_height_positive"),
        CheckConstraint("frame_rate > 0", name="frame_rate_positive"),
        CheckConstraint("progress >= 0 AND progress <= 100", name="progress_range"),
    )

    project: Mapped[Project] = relationship(back_populates="export_jobs")
    output_asset: Mapped[Optional[VideoAsset]] = relationship(back_populates="export_jobs")
    status: Mapped[JobStatus] = relationship(back_populates="export_jobs")


__all__ = [
    "AudioTrack",
    "ExportFormat",
    "ExportJob",
    "JobStatus",
    "JobStatusCode",
    "Project",
    "SceneDetection",
    "SubtitleSegment",
    "TimelineClip",
    "VideoAsset",
    "VideoAssetStatus",
    "VideoAssetType",
]
