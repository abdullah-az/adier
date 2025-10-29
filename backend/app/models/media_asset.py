from __future__ import annotations

from typing import List, Optional

from sqlalchemy import BigInteger, Enum as SQLEnum, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, IDMixin, TimestampMixin
from .enums import MediaAssetType


class MediaAsset(IDMixin, TimestampMixin, Base):
    __tablename__ = "media_assets"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[MediaAssetType] = mapped_column(
        SQLEnum(MediaAssetType, name="media_asset_type_enum"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    analysis_cache: Mapped[Optional[dict[str, object]]] = mapped_column(JSON, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="media_assets")
    source_for_clips: Mapped[List["Clip"]] = relationship(
        back_populates="source_asset",
        foreign_keys="Clip.source_asset_id",
    )
    output_versions: Mapped[List["ClipVersion"]] = relationship(
        back_populates="output_asset",
        foreign_keys="ClipVersion.output_asset_id",
    )


__all__ = ["MediaAsset"]
