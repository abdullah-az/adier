from __future__ import annotations

from typing import Optional
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum as SQLEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, IDMixin, TimestampMixin
from .enums import ProcessingJobStatus, ProcessingJobType


class ProcessingJob(IDMixin, TimestampMixin, Base):
    __tablename__ = "processing_jobs"

    clip_version_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("clip_versions.id", ondelete="SET NULL"), nullable=True
    )
    job_type: Mapped[ProcessingJobType] = mapped_column(
        SQLEnum(ProcessingJobType, name="processing_job_type_enum"), nullable=False
    )
    status: Mapped[ProcessingJobStatus] = mapped_column(
        SQLEnum(ProcessingJobStatus, name="processing_job_status_enum"),
        nullable=False,
        default=ProcessingJobStatus.PENDING,
    )
    queue_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    result_payload: Mapped[Optional[dict[str, object]]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    clip_version: Mapped[Optional["ClipVersion"]] = relationship(
        "ClipVersion", back_populates="jobs", foreign_keys=[clip_version_id]
    )


__all__ = ["ProcessingJob"]
