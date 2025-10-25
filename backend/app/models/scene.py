from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class SceneDetection(BaseModel):
    """Represents a single highlight or scene candidate."""

    id: str
    index: int = Field(ge=0)
    title: str
    description: str
    start_seconds: float = Field(ge=0.0)
    end_seconds: float = Field(ge=0.0)
    start_timecode: str
    end_timecode: str
    highlight_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    recommended_duration: Optional[float] = Field(default=None, ge=0.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SceneAnalysis(BaseModel):
    """Stores the result of a scene detection pass for a video asset."""

    id: str
    project_id: str
    asset_id: str
    model: str
    summary: Optional[str] = None
    status: str = Field(default="completed")
    prompt: dict[str, Any] = Field(default_factory=dict)
    scenes: list[SceneDetection] = Field(default_factory=list)
    usage: dict[str, int] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda value: value.isoformat()}
        use_enum_values = True
