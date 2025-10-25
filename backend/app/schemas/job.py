from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field

from app.models.job import Job, JobLogEntry, JobStatus


class JobCreateRequest(BaseModel):
    job_type: Literal["ingest", "scene_detection", "transcription", "export"] = Field(..., description="Type of job to enqueue")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary payload for the job handler")


class JobLogEntryResponse(BaseModel):
    timestamp: datetime
    level: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_model(cls, entry: JobLogEntry) -> "JobLogEntryResponse":
        return cls.model_validate(entry.model_dump())


class JobResponse(BaseModel):
    id: str
    project_id: str
    job_type: str
    status: JobStatus
    progress: float
    payload: Dict[str, Any]
    result: Dict[str, Any]
    error_message: Optional[str] = None
    logs: list[JobLogEntryResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_model(cls, job: Job) -> "JobResponse":
        payload = job.model_dump()
        payload["logs"] = [JobLogEntryResponse.from_model(entry) for entry in job.logs]
        return cls.model_validate(payload)
