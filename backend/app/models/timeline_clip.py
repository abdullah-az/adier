from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import TimelineTrackType

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.subtitle_segment import SubtitleSegment
    from app.models.video_asset import VideoAsset


class TimelineClip(Base):
    __tablename__ = "timeline_clips"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    video_asset_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("video_assets.id"), nullable=True, index=True
    )
    track_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    track_type: Mapped[TimelineTrackType] = mapped_column(
        String(20), default=TimelineTrackType.VIDEO.value, nullable=False
    )
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    source_start: Mapped[float] = mapped_column(Float, nullable=False)
    source_end: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    muted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    transition_in: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    transition_out: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    effects: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="timeline_clips")
    video_asset: Mapped[Optional["VideoAsset"]] = relationship("VideoAsset", back_populates="timeline_clips")
    subtitles: Mapped[list["SubtitleSegment"]] = relationship(
        "SubtitleSegment", back_populates="timeline_clip", cascade="all, delete-orphan"
    )
