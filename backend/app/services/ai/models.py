from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable


class AICapability(str, Enum):
    """Well known capabilities that AI providers can support."""

    SCENE_ANALYSIS = "scene_analysis"
    TRANSCRIPTION = "transcription"
    HIGHLIGHT_GENERATION = "generate_highlights"
    TEXT_EXTRACTION = "extract_text"


@dataclass(slots=True)
class AIUsage:
    """Basic usage/cost accounting information for AI calls."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    audio_seconds: float = 0.0
    cost: float = 0.0
    requests: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def merge(self, other: "AIUsage") -> "AIUsage":
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.audio_seconds += other.audio_seconds
        self.cost += other.cost
        self.requests += other.requests
        self.metadata.update(other.metadata)
        return self

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "audio_seconds": round(self.audio_seconds, 4),
            "cost": round(self.cost, 6),
            "requests": self.requests,
        }
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload

    def clone(self) -> "AIUsage":
        return AIUsage(
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            audio_seconds=self.audio_seconds,
            cost=self.cost,
            requests=self.requests,
            metadata=dict(self.metadata),
        )


@dataclass(slots=True)
class ProviderAttempt:
    """Record of an individual provider attempt within a fallback chain."""

    provider: str
    status: str
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {"provider": self.provider, "status": self.status}
        if self.error:
            payload["error"] = self.error
        return payload


@dataclass(slots=True)
class ProviderSummary:
    """Summary of the provider execution included with job results."""

    name: str
    display_name: str
    capability: AICapability
    attempts: list[ProviderAttempt] = field(default_factory=list)
    usage: AIUsage = field(default_factory=AIUsage)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "capability": self.capability.value,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "usage": self.usage.to_dict(),
        }

    def with_attempt(self, attempt: ProviderAttempt) -> "ProviderSummary":
        self.attempts.append(attempt)
        return self


def flatten_attempts(attempts: Iterable[ProviderAttempt]) -> list[dict[str, Any]]:
    return [attempt.to_dict() for attempt in attempts]
