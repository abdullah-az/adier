from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, Optional

from loguru import logger

from .exceptions import AIProviderConfigurationError
from .models import AICapability, AIUsage
from .rate_limiter import SlidingWindowRateLimiter


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    name: str
    display_name: str
    capabilities: frozenset[AICapability]

    def __init__(
        self,
        *,
        priority: int = 100,
        rate_limit_per_minute: float | None = None,
    ) -> None:
        self.priority = priority
        self.rate_limit_per_minute = rate_limit_per_minute
        self.display_name = getattr(self, "display_name", self.name.title())
        self._rate_limiter = SlidingWindowRateLimiter(self.name, rate_limit_per_minute)

    def supports(self, capability: AICapability) -> bool:
        return capability in self.capabilities

    def is_configured(self) -> bool:
        return True

    def is_available(self) -> bool:
        return self.is_configured()

    async def _check_rate_limit(self) -> None:
        await self._rate_limiter.acquire()

    async def analyse_scene(self, *args, **kwargs):  # pragma: no cover - defensive alias
        return await self.analyze_scene(*args, **kwargs)

    async def analyze_scene(
        self,
        video_path: Path,
        *,
        project_id: str,
        **kwargs,
    ) -> tuple[list[dict], AIUsage]:
        raise NotImplementedError(f"Provider '{self.name}' does not implement scene analysis")

    async def transcribe_audio(
        self,
        audio_path: Path,
        *,
        project_id: str,
        language: Optional[str] = None,
        **kwargs,
    ) -> tuple[dict, AIUsage]:
        raise NotImplementedError(f"Provider '{self.name}' does not implement transcription")

    async def generate_highlights(
        self,
        transcript: str,
        *,
        project_id: str,
        **kwargs,
    ) -> tuple[dict, AIUsage]:
        raise NotImplementedError(f"Provider '{self.name}' does not implement highlight generation")

    async def extract_text(
        self,
        image_paths: Iterable[Path],
        *,
        project_id: str,
        **kwargs,
    ) -> tuple[dict, AIUsage]:
        raise NotImplementedError(f"Provider '{self.name}' does not implement text extraction")

    def validate_file(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(path)
        if not path.is_file():
            raise AIProviderConfigurationError(f"Expected file path but received '{path}'")

    async def ensure_ready(self) -> None:
        """Allow providers to perform asynchronous initialisation if needed."""
        return None

    def log_configuration(self) -> None:
        logger.debug(
            "Registered AI provider",
            provider=self.name,
            capabilities=sorted(capability.value for capability in self.capabilities),
            priority=self.priority,
        )


class LocalSimulationMixin:
    """Mixin that provides helper methods for providers that simulate responses."""

    @staticmethod
    async def simulate_scene_detection(video_path: Path, *, score: float = 0.91) -> list[dict]:
        from app.utils.ffmpeg import get_video_metadata

        metadata = await get_video_metadata(video_path)
        duration = float(metadata.get("duration") or 0.0)
        if duration <= 0:
            return []
        midpoint = max(round(duration / 2, 2), 0.1)
        return [
            {"timestamp": 0.0, "confidence": round(score, 2)},
            {"timestamp": midpoint, "confidence": round(score * 0.97, 2)},
            {"timestamp": max(duration - 0.1, 0.1), "confidence": round(score * 0.95, 2)},
        ]

    @staticmethod
    async def simulate_transcription(audio_path: Path, *, language: Optional[str] = None) -> dict:
        import asyncio
        import ffmpeg  # type: ignore

        try:
            probe = await asyncio.to_thread(ffmpeg.probe, str(audio_path))
            duration = float(probe.get("format", {}).get("duration", 0.0) or 0.0)
        except Exception:  # pragma: no cover - best effort simulation
            duration = 0.0
        language_code = language or "en"
        return {
            "text": f"Simulated transcript ({duration:.2f}s)",
            "segments": [
                {
                    "text": "Simulated segment",
                    "start": 0.0,
                    "end": max(duration - 0.05, 0.05),
                    "confidence": 0.9,
                }
            ],
            "language": language_code,
        }

    @staticmethod
    def simulated_usage(*, audio_seconds: float = 0.0, prompt_tokens: int = 0, completion_tokens: int = 0) -> AIUsage:
        return AIUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            audio_seconds=audio_seconds,
            cost=0.0,
            requests=1,
        )
