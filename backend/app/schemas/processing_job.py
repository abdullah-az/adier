from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from ..models.enums import ProcessingJobStatus, ProcessingJobType
from .base import TimestampedSchema


class ProcessingJobBase(BaseModel):
    clip_version_id: Optional[str] = None
    job_type: ProcessingJobType
    status: ProcessingJobStatus = ProcessingJobStatus.PENDING
    queue_name: Optional[str] = None
    priority: int = 0
    payload: dict[str, object]
    result_payload: Optional[dict[str, object]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ProcessingJobCreate(ProcessingJobBase):
    pass


class ProcessingJobUpdate(BaseModel):
    status: Optional[ProcessingJobStatus] = None
    queue_name: Optional[str] = None
    priority: Optional[int] = None
    payload: Optional[dict[str, object]] = None
    result_payload: Optional[dict[str, object]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ProcessingJobRead(ProcessingJobBase, TimestampedSchema):
    pass


__all__ = [
    "ProcessingJobBase",
    "ProcessingJobCreate",
    "ProcessingJobUpdate",
    "ProcessingJobRead",
]
