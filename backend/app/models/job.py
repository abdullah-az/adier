from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Enumerated states for background jobs."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobLogEntry(BaseModel):
    """A structured log entry associated with a job."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = Field(default="INFO")
    message: str
    details: dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda value: value.isoformat()}


class Job(BaseModel):
    """Represents an asynchronous processing job."""

    id: str
    project_id: str
    job_type: str
    status: JobStatus = Field(default=JobStatus.QUEUED)
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    payload: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    logs: list[JobLogEntry] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        json_encoders = {datetime: lambda value: value.isoformat()}

    def add_log(self, message: str, level: str = "INFO", **details: Any) -> None:
        entry = JobLogEntry(message=message, level=level, details=details)
        self.logs.append(entry)
        self.updated_at = datetime.utcnow()
