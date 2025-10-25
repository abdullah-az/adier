from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.audio_track import AudioTrack
    from app.models.project import Project
    from app.models.scene_detection import SceneDetection
    from app.models.subtitle_segment import SubtitleSegment
    from app.models.timeline_clip import TimelineClip


class VideoAsset(Base):
    __tablename__ = "video_assets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    codec: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="video_assets")
    scenes: Mapped[list["SceneDetection"]] = relationship(
        "SceneDetection", back_populates="video_asset", cascade="all, delete-orphan"
    )
    timeline_clips: Mapped[list["TimelineClip"]] = relationship(
        "TimelineClip", back_populates="video_asset", cascade="all, delete-orphan"
    )
    audio_tracks: Mapped[list["AudioTrack"]] = relationship(
        "AudioTrack", back_populates="video_asset", cascade="all, delete-orphan"
    )
    subtitles: Mapped[list["SubtitleSegment"]] = relationship(
        "SubtitleSegment", back_populates="video_asset", cascade="all, delete-orphan"
    )
