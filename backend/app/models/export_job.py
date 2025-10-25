from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ExportJobStatus, ExportJobType

if TYPE_CHECKING:
    from app.models.job_progress import JobProgress
    from app.models.project import Project


class ExportJob(Base):
    __tablename__ = "export_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    job_type: Mapped[ExportJobType] = mapped_column(String(20), nullable=False)
    status: Mapped[ExportJobStatus] = mapped_column(
        String(20), default=ExportJobStatus.PENDING.value, nullable=False, index=True
    )
    output_format: Mapped[str] = mapped_column(String(50), nullable=False)
    output_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    bitrate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="export_jobs")
    progress_logs: Mapped[list["JobProgress"]] = relationship(
        "JobProgress", back_populates="export_job", cascade="all, delete-orphan"
    )
