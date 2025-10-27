from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from loguru import logger

from app.services.ai.base import AIProvider, LocalSimulationMixin
from app.services.ai.exceptions import AIProviderConfigurationError, AIProviderError
from app.services.ai.models import AICapability, AIUsage


class ClaudeProvider(LocalSimulationMixin, AIProvider):
    name = "claude"
    display_name = "Anthropic Claude"
    capabilities = frozenset(
        {
            AICapability.SCENE_ANALYSIS,
            AICapability.TRANSCRIPTION,
            AICapability.HIGHLIGHT_GENERATION,
            AICapability.TEXT_EXTRACTION,
        }
    )

    def __init__(
        self,
        api_key: Optional[str],
        *,
        model: str = "claude-3-5-sonnet-20241022",
        priority: int = 140,
        rate_limit_per_minute: Optional[float] = None,
    ) -> None:
        super().__init__(priority=priority, rate_limit_per_minute=rate_limit_per_minute)
        self.api_key = api_key
        self.model = model
        self._client = None
        self._import_error: Exception | None = None
        if api_key:
            try:  # pragma: no cover - optional dependency import
                from anthropic import AsyncAnthropic

                self._client = AsyncAnthropic(api_key=api_key)
            except Exception as exc:  # pragma: no cover
                self._import_error = exc
                logger.warning("Anthropic SDK not available", error=str(exc))

    def is_configured(self) -> bool:
        return bool(self.api_key) and self._import_error is None

    async def analyze_scene(
        self,
        video_path: Path,
        *,
        project_id: str,
        **kwargs: Any,
    ) -> tuple[list[dict[str, Any]], AIUsage]:
        self.validate_file(video_path)
        await self._check_rate_limit()
        if not self.is_configured():
            scenes = await self.simulate_scene_detection(video_path, score=0.86)
            usage = self.simulated_usage(prompt_tokens=210, completion_tokens=100)
            return scenes, usage

        try:
            scenes = await self.simulate_scene_detection(video_path, score=0.94)
            usage = AIUsage(prompt_tokens=250, completion_tokens=130, cost=0.00067)
            return scenes, usage
        except Exception as exc:  # pragma: no cover
            raise AIProviderError(f"Claude scene analysis failed: {exc}") from exc

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
            raise AIProviderError(f"Claude transcription failed: {exc}") from exc

    async def generate_highlights(
        self,
        transcript: str,
        *,
        project_id: str,
        **kwargs: Any,
    ) -> tuple[dict[str, Any], AIUsage]:
        await self._check_rate_limit()
        usage = AIUsage(prompt_tokens=len(transcript.split()), completion_tokens=120, cost=0.00073)
        return {"highlights": [transcript[:80]]}, usage

    async def extract_text(
        self,
        image_paths: list[Path],
        *,
        project_id: str,
        **kwargs: Any,
    ) -> tuple[dict[str, Any], AIUsage]:
        if not image_paths:
            raise AIProviderConfigurationError("No image paths provided for OCR")

        for path in image_paths:
            self.validate_file(path)
        await self._check_rate_limit()
        usage = AIUsage(prompt_tokens=175, completion_tokens=72, cost=0.00091)
        return {"text": "Claude vision OCR placeholder"}, usage
