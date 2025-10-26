from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class SceneDetection(BaseModel):
    """Represents a single AI-generated highlight or scene recommendation."""

    id: str = Field(..., description="Unique identifier for the scene recommendation")
    asset_id: str = Field(..., description="Video asset identifier")
    project_id: str = Field(..., description="Project identifier")
    title: str = Field(..., min_length=1, description="Short label for the highlight")
    description: str = Field(..., min_length=1, description="Narrative description of why the scene matters")
    start: float = Field(..., ge=0.0, description="Start timestamp in seconds")
    end: float = Field(..., ge=0.0, description="End timestamp in seconds")
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Model provided confidence score for this highlight",
    )
    priority: Optional[int] = Field(
        default=None,
        ge=1,
        description="Ranking to help editors prioritise scenes (1 is highest priority)",
    )
    tags: list[str] = Field(default_factory=list, description="Curated tags describing the scene")
    request_id: str = Field(..., description="Identifier of the scene analysis run")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Provider specific metadata and scoring")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def duration(self) -> float:
        return max(self.end - self.start, 0.0)


class SceneDetectionRun(BaseModel):
    """Container describing a full scene detection analysis run."""

    id: str = Field(..., description="Identifier for the analysis run")
    asset_id: str = Field(..., description="Video asset identifier")
    project_id: str = Field(..., description="Project identifier")
    tone: Optional[str] = Field(default=None, description="Requested storytelling tone")
    criteria: Optional[str] = Field(default=None, description="Highlight selection criteria")
    max_scenes: Optional[int] = Field(default=None, ge=1, description="Maximum number of highlights requested")
    source_model: str = Field(default="gpt-4o-mini", description="Model used for the analysis")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Prompt configuration for caching")
    usage: dict[str, Any] = Field(default_factory=dict, description="Token usage metadata")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata returned by the model")
    scenes: list[SceneDetection] = Field(default_factory=list, description="Ordered list of generated highlights")

    @property
    def scene_count(self) -> int:
        return len(self.scenes)


__all__ = ["SceneDetection", "SceneDetectionRun"]
