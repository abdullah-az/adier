from __future__ import annotations

from typing import List, Optional

from sqlalchemy import JSON, Enum as SQLEnum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, IDMixin, TimestampMixin
from .enums import PresetCategory


class Preset(IDMixin, TimestampMixin, Base):
    __tablename__ = "presets"

    key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[PresetCategory] = mapped_column(
        SQLEnum(PresetCategory, name="preset_category_enum"), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    configuration: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    clip_versions: Mapped[List["ClipVersion"]] = relationship(back_populates="preset")


__all__ = ["Preset"]
