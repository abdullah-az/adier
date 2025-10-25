from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import ExportJobStatus


class JobProgressBase(BaseModel):
    export_job_id: int = Field(..., description="Associated export job ID")
    status: ExportJobStatus = Field(..., description="Status at this log entry")
    progress: float = Field(..., ge=0, le=100, description="Progress percentage")
    message: Optional[str] = Field(None, description="Status message")
    job_metadata: Optional[str] = Field(None, description="Additional metadata")


class JobProgressCreate(JobProgressBase):
    pass


class JobProgressResponse(JobProgressBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
