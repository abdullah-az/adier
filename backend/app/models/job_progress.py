from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ExportJobStatus

if TYPE_CHECKING:
    from app.models.export_job import ExportJob


class JobProgress(Base):
    __tablename__ = "job_progress_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    export_job_id: Mapped[int] = mapped_column(ForeignKey("export_jobs.id"), nullable=False, index=True)
    status: Mapped[ExportJobStatus] = mapped_column(String(20), nullable=False)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    job_metadata: Mapped[Optional[str]] = mapped_column("metadata", Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    export_job: Mapped["ExportJob"] = relationship("ExportJob", back_populates="progress_logs")
