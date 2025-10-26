from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.db.models import ExportFormat, JobStatusCode
from app.schemas.job_status import JobStatusRead


class ExportJobBase(BaseModel):
    output_asset_id: Optional[str] = Field(default=None, min_length=1)
    format: ExportFormat
    preset: Optional[str] = Field(default=None, max_length=64)
    resolution_width: int = Field(default=1920, ge=1, le=8192)
    resolution_height: int = Field(default=1080, ge=1, le=8192)
    frame_rate: float = Field(default=24.0, gt=0, le=240)
    progress: float = Field(default=0.0, ge=0, le=100)
    output_path: Optional[str] = Field(default=None, max_length=512)
    error_message: Optional[str] = Field(default=None, max_length=2000)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExportJobCreate(ExportJobBase):
    project_id: str = Field(..., min_length=1)
    status_id: Optional[int] = None
    status_code: JobStatusCode = Field(default=JobStatusCode.QUEUED)


class ExportJobUpdate(BaseModel):
    output_asset_id: Optional[str] = Field(default=None, min_length=1)
    format: Optional[ExportFormat] = None
    preset: Optional[str] = Field(default=None, max_length=64)
    resolution_width: Optional[int] = Field(default=None, ge=1, le=8192)
    resolution_height: Optional[int] = Field(default=None, ge=1, le=8192)
    frame_rate: Optional[float] = Field(default=None, gt=0, le=240)
    status_id: Optional[int] = None
    status_code: Optional[JobStatusCode] = None
    progress: Optional[float] = Field(default=None, ge=0, le=100)
    output_path: Optional[str] = Field(default=None, max_length=512)
    error_message: Optional[str] = Field(default=None, max_length=2000)
    metadata: Optional[Dict[str, Any]] = None


class ExportJobRead(ExportJobBase):
    id: str
    project_id: str
    status_id: int
    status: Optional[JobStatusRead] = None
    status_code: Optional[JobStatusCode] = None
    requested_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def _populate_status_code(self) -> "ExportJobRead":
        if self.status is not None and self.status_code is None:
            self.status_code = self.status.code
        return self
