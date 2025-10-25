from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.job import JobStatus


class ProjectAssetSummary(BaseModel):
    asset_id: str = Field(..., description="Unique identifier for the asset")
    filename: str = Field(..., description="Stored filename of the asset")
    original_filename: str = Field(..., description="Original filename supplied by the user")
    size_bytes: int = Field(..., ge=0, description="Size of the asset in bytes")
    status: str = Field(..., description="Processing status for the asset")
    updated_at: datetime = Field(..., description="Timestamp of the most recent update")


class ProjectJobSummary(BaseModel):
    id: str = Field(..., description="Unique identifier for the job")
    job_type: str = Field(..., description="Type of job that was created")
    status: JobStatus = Field(..., description="Current status of the job")
    progress: float = Field(..., ge=0.0, le=100.0, description="Progress percentage for the job")
    updated_at: datetime = Field(..., description="Timestamp of the most recent update")
    error_message: Optional[str] = Field(default=None, description="Optional error message when the job fails")


class ProjectSummaryResponse(BaseModel):
    project_id: str = Field(..., description="Project identifier")
    display_name: str = Field(..., description="Display name that should be shown in the UI")
    status: str = Field(..., description="High level project status flag")
    updated_at: datetime = Field(..., description="Timestamp of the last update across assets or jobs")
    asset_count: int = Field(..., ge=0, description="Number of assets associated with the project")
    total_size_bytes: int = Field(..., ge=0, description="Total size across all assets")
    job_progress: float = Field(0.0, ge=0.0, le=100.0, description="Progress for the most recent active job")
    thumbnail_url: Optional[str] = Field(None, description="URL that can be used to retrieve the latest thumbnail")
    latest_asset: Optional[ProjectAssetSummary] = Field(
        default=None,
        description="Metadata for the most recent asset uploaded in the project",
    )
    latest_job: Optional[ProjectJobSummary] = Field(
        default=None,
        description="Metadata for the most recent job executed for the project",
    )

    model_config = {"json_encoders": {datetime: lambda value: value.isoformat()}}
