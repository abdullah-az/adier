from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ProviderUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    audio_seconds: float = 0.0
    cost: float = 0.0
    requests: int = 0
    metadata: Dict[str, Any] | None = None


class ProviderInfoResponse(BaseModel):
    name: str
    display_name: str
    priority: int
    capabilities: list[str]
    configured: bool
    available: bool
    rate_limit_per_minute: float | None = Field(default=None)
    usage: ProviderUsage


class ProviderPreferenceResponse(BaseModel):
    project_id: str
    preferences: Dict[str, str] = Field(default_factory=dict)


class ProviderPreferenceUpdate(BaseModel):
    preferences: Dict[str, Optional[str]] = Field(default_factory=dict)
