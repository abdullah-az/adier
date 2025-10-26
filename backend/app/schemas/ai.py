from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class SubtitleSegmentSchema(BaseModel):
    index: int = Field(..., ge=0)
    start: float = Field(..., ge=0.0)
    end: float = Field(..., ge=0.0)
    duration: float = Field(..., ge=0.0)
    text: str = Field(..., min_length=1)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    language: Optional[str] = None
    speaker: Optional[str] = None

    model_config = {
        "from_attributes": True,
    }


class SubtitleTranscriptResponse(BaseModel):
    asset_id: str
    project_id: str
    request_id: str
    language: str
    text: str
    segment_count: int
    duration: float
    usage: dict[str, Any]
    segments: list[SubtitleSegmentSchema]
    cached: bool = False
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "from_attributes": True,
    }


class SceneDetectionSchema(BaseModel):
    id: str
    title: str
    description: str
    start: float = Field(..., ge=0.0)
    end: float = Field(..., ge=0.0)
    duration: float = Field(..., ge=0.0)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    priority: Optional[int] = Field(default=None, ge=1)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "from_attributes": True,
    }


class SceneDetectionResponse(BaseModel):
    asset_id: str
    project_id: str
    request_id: str
    generated_at: datetime
    parameters: dict[str, Any] = Field(default_factory=dict)
    usage: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    scenes: list[SceneDetectionSchema] = Field(default_factory=list)

    model_config = {
        "from_attributes": True,
    }


__all__ = [
    "SubtitleSegmentSchema",
    "SubtitleTranscriptResponse",
    "SceneDetectionSchema",
    "SceneDetectionResponse",
]
