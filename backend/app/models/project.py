from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from app.models.pipeline import (
    BackgroundMusicSpec,
    SubtitleSpec,
    TimelineCompositionRequest,
)


def generate_timeline_id() -> str:
    return f"timeline_{uuid4().hex}"


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    EDITING = "editing"
    READY = "ready"
    ARCHIVED = "archived"


class ClipTiming(BaseModel):
    """Represents the runtime positioning of a clip within a timeline."""

    clip_id: str = Field(..., description="Client-specified identifier for the clip")
    asset_id: str = Field(..., description="Source video asset identifier")
    start: float = Field(..., ge=0.0, description="Timeline start in seconds")
    duration: float = Field(..., gt=0.0, description="Duration of the clip on the timeline")
    in_point: float = Field(default=0.0, ge=0.0, description="Source media in-point in seconds")
    out_point: Optional[float] = Field(default=None, ge=0.0, description="Source media out-point in seconds")
    include_audio: bool = Field(default=True, description="Whether the clip's native audio is used")
    label: Optional[str] = Field(default=None, description="Friendly label displayed in timeline editors")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary clip level metadata")


class TimelineState(BaseModel):
    """Stores the authored timeline plus the working composition payload."""

    timeline_id: str = Field(default_factory=generate_timeline_id)
    locale: str = Field(default="en-US", description="Locale associated with this timeline edit")
    layout: list[ClipTiming] = Field(default_factory=list, description="Clip ordering and positioning")
    composition: TimelineCompositionRequest
    total_duration: float = Field(..., ge=0.0, description="Overall runtime of the timeline")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional editor metadata")
    last_preview_job_id: Optional[str] = Field(default=None)
    last_export_job_id: Optional[str] = Field(default=None)
    global_subtitles: Optional[SubtitleSpec] = Field(default=None)
    background_music: Optional[BackgroundMusicSpec] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Project(BaseModel):
    """Aggregate representing the end-to-end video editing project."""

    id: str
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.DRAFT
    primary_locale: str = Field(default="en-US", description="Primary locale for the project")
    supported_locales: list[str] = Field(default_factory=lambda: ["en-US"])
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    timeline: Optional[TimelineState] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "json_encoders": {datetime: lambda value: value.isoformat()},
    }


__all__ = [
    "Project",
    "ProjectStatus",
    "TimelineState",
    "ClipTiming",
]
