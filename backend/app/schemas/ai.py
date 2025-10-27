from __future__ import annotations

from typing import Any, List

from pydantic import BaseModel, Field


class AISuggestionRequest(BaseModel):
    locale: str = Field(default="en-US", example="en-US")
    limit: int = Field(default=6, ge=1, le=25, example=6)


class AISceneSuggestion(BaseModel):
    scene_id: str
    asset_id: str
    start: float
    end: float
    duration: float
    confidence: float
    locale: str
    title: str
    description: str
    tags: List[str]
    metadata: dict[str, Any]


class AISuggestionResponse(BaseModel):
    locale: str
    generated_at: str
    scenes: List[AISceneSuggestion]
    source_assets: List[dict[str, Any]]
