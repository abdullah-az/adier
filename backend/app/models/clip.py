from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Enum as SQLEnum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, IDMixin, TimestampMixin
from .enums import ClipStatus, ClipVersionStatus


class Clip(IDMixin, TimestampMixin, Base):
    __tablename__ = "clips"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    source_asset_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ClipStatus] = mapped_column(
        SQLEnum(ClipStatus, name="clip_status_enum"), default=ClipStatus.DRAFT, nullable=False
    )
    start_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    end_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="clips")
    source_asset: Mapped[Optional["MediaAsset"]] = relationship(
        "MediaAsset",
        back_populates="source_for_clips",
        foreign_keys=[source_asset_id],
    )
    versions: Mapped[List["ClipVersion"]] = relationship(
        back_populates="clip", cascade="all, delete-orphan", order_by="ClipVersion.version_number"
    )


class ClipVersion(IDMixin, TimestampMixin, Base):
    __tablename__ = "clip_versions"

    clip_id: Mapped[str] = mapped_column(ForeignKey("clips.id", ondelete="CASCADE"), nullable=False)
    output_asset_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True
    )
    preset_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("presets.id", ondelete="SET NULL"), nullable=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[ClipVersionStatus] = mapped_column(
        SQLEnum(ClipVersionStatus, name="clip_version_status_enum"),
        default=ClipVersionStatus.DRAFT,
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    plan_metadata: Mapped[Optional[dict[str, object]]] = mapped_column(JSON, nullable=True)

    clip: Mapped[Clip] = relationship(back_populates="versions")
    output_asset: Mapped[Optional["MediaAsset"]] = relationship(
        "MediaAsset",
        back_populates="output_versions",
        foreign_keys=[output_asset_id],
    )
    preset: Mapped[Optional["Preset"]] = relationship("Preset", back_populates="clip_versions")
    jobs: Mapped[List["ProcessingJob"]] = relationship(
        "ProcessingJob", back_populates="clip_version", cascade="all, delete-orphan"
    )


__all__ = ["Clip", "ClipVersion"]
