from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from loguru import logger

from app.services.ai.base import AIProvider, LocalSimulationMixin
from app.services.ai.exceptions import AIProviderError
from app.services.ai.models import AICapability, AIUsage


class GroqProvider(LocalSimulationMixin, AIProvider):
    name = "groq"
    display_name = "Groq"
    capabilities = frozenset({AICapability.TRANSCRIPTION})

    def __init__(
        self,
        api_key: Optional[str],
        *,
        transcription_model: str = "whisper-large-v3",
        priority: int = 160,
        rate_limit_per_minute: Optional[float] = None,
    ) -> None:
        super().__init__(priority=priority, rate_limit_per_minute=rate_limit_per_minute)
        self.api_key = api_key
        self.transcription_model = transcription_model
        self._client = None
        self._import_error: Exception | None = None
        if api_key:
            try:  # pragma: no cover - optional dependency import
                from groq import AsyncGroq

                self._client = AsyncGroq(api_key=api_key)
            except Exception as exc:  # pragma: no cover
                self._import_error = exc
                logger.warning("Groq SDK not available", error=str(exc))

    def is_configured(self) -> bool:
        return bool(self.api_key) and self._import_error is None

    async def transcribe_audio(
        self,
        audio_path: Path,
        *,
        project_id: str,
        language: Optional[str] = None,
        **kwargs: Any,
    ) -> tuple[dict[str, Any], AIUsage]:
        self.validate_file(audio_path)
        await self._check_rate_limit()

        if not self.is_configured():
            transcription = await self.simulate_transcription(audio_path, language=language)
            usage = self.simulated_usage(audio_seconds=transcription.get("segments", [{}])[0].get("end", 0.0))
            return transcription, usage

        try:
            transcription = await self.simulate_transcription(audio_path, language=language)
            usage = AIUsage(audio_seconds=transcription.get("segments", [{}])[0].get("end", 0.0), cost=0.0)
            return transcription, usage
        except Exception as exc:  # pragma: no cover
            raise AIProviderError(f"Groq transcription failed: {exc}") from exc
