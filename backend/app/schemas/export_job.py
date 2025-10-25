from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, constr

from app.models.enums import ExportJobStatus, ExportJobType


class ExportJobBase(BaseModel):
    project_id: int = Field(..., description="Associated project ID")
    job_type: ExportJobType = Field(..., description="Type of export job")
    output_format: constr(min_length=1, max_length=50) = Field(..., description="Output file format")
    resolution: Optional[str] = Field(None, max_length=20, description="Output resolution (e.g., '1920x1080')")
    bitrate: Optional[int] = Field(None, gt=0, description="Output bitrate in kbps")
    fps: Optional[int] = Field(None, gt=0, description="Output frames per second")


class ExportJobCreate(ExportJobBase):
    pass


class ExportJobUpdate(BaseModel):
    status: Optional[ExportJobStatus] = None
    output_path: Optional[str] = Field(None, max_length=512)
    progress: Optional[float] = Field(None, ge=0, le=100)
    error_message: Optional[str] = None


class ExportJobResponse(ExportJobBase):
    id: int
    status: ExportJobStatus
    output_path: Optional[str]
    progress: float
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
