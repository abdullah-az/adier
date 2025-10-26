"""Core abstractions and shared models for AI provider integrations."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Optional


class ProviderTask(str, Enum):
    """Canonical tasks that AI providers may support."""

    SCENE_ANALYSIS = "scene_analysis"
    TRANSCRIPTION = "transcription"
    HIGHLIGHT_GENERATION = "highlight_generation"
    TEXT_EXTRACTION = "text_extraction"


@dataclass(slots=True)
class ProviderResult:
    """Container for results returned by providers."""

    data: dict[str, Any]
    cost: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    raw: Any | None = None


class ProviderError(RuntimeError):
    """Base exception for provider issues."""


class ProviderNotConfiguredError(ProviderError):
    """Raised when a provider is initialised without the required credentials."""


class ProviderCapabilityNotSupportedError(ProviderError):
    """Raised when a provider does not implement the requested task."""


class ProviderRateLimitError(ProviderError):
    """Raised when a provider indicates the request should be retried later."""

    def __init__(self, message: str, *, retry_after: Optional[float] = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class ProviderQuotaError(ProviderError):
    """Raised when the account has exhausted quota for the provider."""


class ProviderInvocationError(ProviderError):
    """Raised when the provider fails to fulfil the request due to other reasons."""


class ProviderUnavailableError(ProviderError):
    """Raised when no provider in the configured chain can service the request."""

    def __init__(self, task: ProviderTask, attempts: Iterable[dict[str, Any]]) -> None:
        attempts_list = list(attempts)
        super().__init__(
            f"No AI providers were able to complete task '{task.value}'. Attempts: {attempts_list!r}"
        )
        self.task = task
        self.attempts = attempts_list


class AIProvider(ABC):
    """Abstract base class encapsulating AI provider integrations."""

    provider_id: str = "base"
    display_name: str = "Base Provider"
    capabilities: frozenset[ProviderTask] = frozenset()
    cost_currency: str = "USD"

    def __init__(self, *, rate_limits: Optional[dict[str, Any]] = None) -> None:
        self.rate_limits = rate_limits or {}
        self._configured: bool = False

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------
    def supports(self, task: ProviderTask) -> bool:
        return task in self.capabilities

    def is_available(self) -> bool:
        return self._configured

    def describe(self) -> dict[str, Any]:
        return {
            "id": self.provider_id,
            "name": self.display_name,
            "capabilities": sorted(task.value for task in self.capabilities),
            "configured": self._configured,
            "available": self.is_available(),
            "rate_limits": self.rate_limits,
            "cost_currency": self.cost_currency,
        }

    def _ensure_configured(self) -> None:
        if not self._configured:
            raise ProviderNotConfiguredError(
                f"Provider '{self.provider_id}' is not configured. Check environment variables and credentials."
            )

    def _ensure_capability(self, task: ProviderTask) -> None:
        if not self.supports(task):
            raise ProviderCapabilityNotSupportedError(
                f"Provider '{self.provider_id}' does not support task '{task.value}'"
            )

    async def warmup(self) -> None:  # pragma: no cover - opt-in hook for subclasses
        """Allow providers to perform lazy initialisation work."""
        return None

    # ------------------------------------------------------------------
    # Provider contract
    # ------------------------------------------------------------------
    @abstractmethod
    async def analyze_scene(self, *, video_frames: list[Any], transcript: Optional[str] = None, **kwargs: Any) -> ProviderResult:
        raise ProviderCapabilityNotSupportedError("Scene analysis not implemented")

    @abstractmethod
    async def transcribe_audio(self, *, audio_source: Any, language: Optional[str] = None, **kwargs: Any) -> ProviderResult:
        raise ProviderCapabilityNotSupportedError("Transcription not implemented")

    @abstractmethod
    async def generate_highlights(self, *, transcript: str, metadata: Optional[dict[str, Any]] = None, **kwargs: Any) -> ProviderResult:
        raise ProviderCapabilityNotSupportedError("Highlight generation not implemented")

    @abstractmethod
    async def extract_text(self, *, document: Any, **kwargs: Any) -> ProviderResult:
        raise ProviderCapabilityNotSupportedError("Text extraction not implemented")


class LocalFallbackProvider(AIProvider):
    """Deterministic provider used as a last-resort fallback for offline flows."""

    provider_id = "local"
    display_name = "Local Mock Models"
    capabilities = frozenset(
        {
            ProviderTask.SCENE_ANALYSIS,
            ProviderTask.TRANSCRIPTION,
            ProviderTask.HIGHLIGHT_GENERATION,
            ProviderTask.TEXT_EXTRACTION,
        }
    )

    def __init__(self) -> None:
        super().__init__()
        self._configured = True

    async def analyze_scene(self, *, video_frames: list[Any], transcript: Optional[str] = None, **kwargs: Any) -> ProviderResult:
        scene_count = max(1, min(len(video_frames) // 5, 20)) if video_frames else 3
        scenes = [
            {
                "timestamp": index * 5,
                "confidence": round(0.8 + (index / max(scene_count, 1)) * 0.15, 3),
                "summary": f"Simulated scene {index + 1}",
            }
            for index in range(scene_count)
        ]
        if transcript:
            scenes[0]["summary"] = transcript.split(".")[0][:120] or scenes[0]["summary"]
        metadata = {"provider": self.provider_id, "frame_samples": len(video_frames)}
        return ProviderResult(data={"scenes": scenes}, metadata=metadata)

    async def transcribe_audio(self, *, audio_source: Any, language: Optional[str] = None, **kwargs: Any) -> ProviderResult:
        transcript = "Simulated transcript generated locally."
        if isinstance(audio_source, bytes):
            transcript = f"Local transcript ({len(audio_source)} bytes)"
        metadata = {"provider": self.provider_id, "language": language or "en"}
        return ProviderResult(data={"transcript": transcript, "language": language or "en"}, metadata=metadata)

    async def generate_highlights(self, *, transcript: str, metadata: Optional[dict[str, Any]] = None, **kwargs: Any) -> ProviderResult:
        sentences = [sentence.strip() for sentence in transcript.split(".") if sentence.strip()]
        highlights = sentences[:3] if sentences else [transcript[:140]]
        meta = {"provider": self.provider_id}
        if metadata:
            meta.update(metadata)
        return ProviderResult(data={"highlights": highlights}, metadata=meta)

    async def extract_text(self, *, document: Any, **kwargs: Any) -> ProviderResult:
        if isinstance(document, str):
            content = document
        elif isinstance(document, bytes):
            content = document.decode("utf-8", errors="ignore")
        else:
            content = ""
        return ProviderResult(data={"text": content.strip()}, metadata={"provider": self.provider_id})
