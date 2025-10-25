from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class SceneSuggestionRequest(BaseModel):
    """Request payload for AI scene suggestions."""

    asset_id: str = Field(..., description="Identifier of the asset to analyse")
    max_suggestions: int = Field(default=5, ge=1, le=15)
    target_duration: Optional[float] = Field(default=None, gt=0.0)
    locale: str = Field(default="en")
    focus_keywords: list[str] = Field(default_factory=list)


class SceneSuggestion(BaseModel):
    id: str
    asset_id: str
    start: float
    end: float
    confidence: float
    title: str
    description: str
    locale: str
    keywords: list[str] = Field(default_factory=list)


class SceneSuggestionResponse(BaseModel):
    suggestions: List[SceneSuggestion]


__all__ = [
    "SceneSuggestionRequest",
    "SceneSuggestion",
    "SceneSuggestionResponse",
]
