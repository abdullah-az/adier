from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.pipeline import AspectRatio, ResolutionPreset
from app.models.project import Project


class ProjectCreateRequest(BaseModel):
    """Payload for creating a new project."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    locale: str = Field(default="en", description="Primary locale code")
    status: str = Field(default="draft")
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    default_aspect_ratio: AspectRatio = Field(default=AspectRatio.SIXTEEN_NINE)
    default_resolution: ResolutionPreset = Field(default=ResolutionPreset.P1080)


class ProjectUpdateRequest(BaseModel):
    """Partial update payload for projects."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    locale: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)
    tags: Optional[list[str]] = Field(default=None)
    metadata: Optional[dict[str, Any]] = Field(default=None)
    default_aspect_ratio: Optional[AspectRatio] = Field(default=None)
    default_resolution: Optional[ResolutionPreset] = Field(default=None)


class ProjectSummary(BaseModel):
    """Summary information for project listings."""

    id: str
    name: str
    locale: str
    status: str
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    timeline_count: int = Field(default=0)

    @classmethod
    def from_model(cls, project: Project) -> "ProjectSummary":
        return cls(
            id=project.id,
            name=project.name,
            locale=project.locale,
            status=project.status,
            tags=project.tags,
            created_at=project.created_at,
            updated_at=project.updated_at,
            timeline_count=len(project.timeline_ids),
        )


class ProjectResponse(ProjectSummary):
    """Detailed representation of a project."""

    description: Optional[str]
    metadata: dict[str, Any] = Field(default_factory=dict)
    default_aspect_ratio: AspectRatio
    default_resolution: ResolutionPreset
    last_opened_at: Optional[datetime] = None

    @classmethod
    def from_model(cls, project: Project) -> "ProjectResponse":
        summary = ProjectSummary.from_model(project)
        return cls(
            **summary.model_dump(),
            description=project.description,
            metadata=project.metadata,
            default_aspect_ratio=project.default_aspect_ratio,
            default_resolution=project.default_resolution,
            last_opened_at=project.last_opened_at,
        )


__all__ = [
    "ProjectCreateRequest",
    "ProjectUpdateRequest",
    "ProjectSummary",
    "ProjectResponse",
]
