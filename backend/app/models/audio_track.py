from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AudioTrackType

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.video_asset import VideoAsset


class AudioTrack(Base):
    __tablename__ = "audio_tracks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    video_asset_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("video_assets.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    track_type: Mapped[AudioTrackType] = mapped_column(
        String(20), default=AudioTrackType.VOICE_OVER.value, nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    volume: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    sample_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    channels: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    codec: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="audio_tracks")
    video_asset: Mapped[Optional["VideoAsset"]] = relationship("VideoAsset", back_populates="audio_tracks")
