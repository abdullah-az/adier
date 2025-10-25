from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import SubtitleFormat

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.timeline_clip import TimelineClip
    from app.models.video_asset import VideoAsset


class SubtitleSegment(Base):
    __tablename__ = "subtitle_segments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    video_asset_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("video_assets.id"), nullable=True, index=True
    )
    timeline_clip_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("timeline_clips.id"), nullable=True, index=True
    )
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    format: Mapped[SubtitleFormat] = mapped_column(String(20), default=SubtitleFormat.SRT.value, nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    speaker: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="subtitle_segments")
    video_asset: Mapped[Optional["VideoAsset"]] = relationship("VideoAsset", back_populates="subtitles")
    timeline_clip: Mapped[Optional["TimelineClip"]] = relationship(
        "TimelineClip", back_populates="subtitles"
    )
