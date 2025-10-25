from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ProjectStatus


if TYPE_CHECKING:
    from app.models.audio_track import AudioTrack
    from app.models.background_music import BackgroundMusic
    from app.models.export_job import ExportJob
    from app.models.scene_detection import SceneDetection
    from app.models.subtitle_segment import SubtitleSegment
    from app.models.timeline_clip import TimelineClip
    from app.models.video_asset import VideoAsset


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status"),
        default=ProjectStatus.DRAFT,
        nullable=False,
        index=True,
    )
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    project_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    video_assets: Mapped[list["VideoAsset"]] = relationship(
        "VideoAsset", back_populates="project", cascade="all, delete-orphan"
    )
    scenes: Mapped[list["SceneDetection"]] = relationship(
        "SceneDetection", back_populates="project", cascade="all, delete-orphan"
    )
    subtitle_segments: Mapped[list["SubtitleSegment"]] = relationship(
        "SubtitleSegment", back_populates="project", cascade="all, delete-orphan"
    )
    timeline_clips: Mapped[list["TimelineClip"]] = relationship(
        "TimelineClip", back_populates="project", cascade="all, delete-orphan"
    )
    audio_tracks: Mapped[list["AudioTrack"]] = relationship(
        "AudioTrack", back_populates="project", cascade="all, delete-orphan"
    )
    background_music: Mapped[list["BackgroundMusic"]] = relationship(
        "BackgroundMusic", back_populates="project", cascade="all, delete-orphan"
    )
    export_jobs: Mapped[list["ExportJob"]] = relationship(
        "ExportJob", back_populates="project", cascade="all, delete-orphan"
    )
