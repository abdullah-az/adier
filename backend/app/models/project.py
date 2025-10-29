from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Enum as SQLEnum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, IDMixin, TimestampMixin
from .enums import ProjectStatus


class Project(IDMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        SQLEnum(ProjectStatus, name="project_status_enum"), default=ProjectStatus.ACTIVE, nullable=False
    )
    storage_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    media_assets: Mapped[List["MediaAsset"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    clips: Mapped[List["Clip"]] = relationship(back_populates="project", cascade="all, delete-orphan")


__all__ = ["Project"]
