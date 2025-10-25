from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.pipeline import AspectRatio, ResolutionPreset


class Project(BaseModel):
    """Domain model representing a video editing project."""

    id: str = Field(..., description="Unique project identifier")
    name: str = Field(..., description="Display name for the project")
    description: Optional[str] = Field(default=None, description="Optional project description")
    locale: str = Field(default="en", description="Primary locale for localisation aware flows")
    status: str = Field(default="draft", description="Lifecycle status (draft, active, archived)")
    tags: list[str] = Field(default_factory=list, description="Arbitrary project tags for filtering")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata provided by clients")
    default_aspect_ratio: AspectRatio = Field(default=AspectRatio.SIXTEEN_NINE)
    default_resolution: ResolutionPreset = Field(default=ResolutionPreset.P1080)
    timeline_ids: list[str] = Field(default_factory=list, description="Associated timeline identifiers")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_opened_at: Optional[datetime] = Field(default=None)

    model_config = {"json_encoders": {datetime: lambda value: value.isoformat()}}


__all__ = ["Project"]
