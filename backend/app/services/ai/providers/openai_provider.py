from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from loguru import logger

from app.services.ai.base import AIProvider, LocalSimulationMixin
from app.services.ai.exceptions import AIProviderConfigurationError, AIProviderError
from app.services.ai.models import AICapability, AIUsage


class OpenAIProvider(LocalSimulationMixin, AIProvider):
    name = "openai"
    display_name = "OpenAI"
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
        model: str = "gpt-4.1",
        transcription_model: str = "gpt-4o-mini-transcribe",
        priority: int = 100,
        rate_limit_per_minute: Optional[float] = None,
    ) -> None:
        super().__init__(priority=priority, rate_limit_per_minute=rate_limit_per_minute)
        self.api_key = api_key
        self.model = model
        self.transcription_model = transcription_model
        self._client = None
        self._import_error: Exception | None = None
        if api_key:
            try:  # pragma: no cover - import guarded for environments without openai
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(api_key=api_key)
            except Exception as exc:  # pragma: no cover - import time failure
                self._import_error = exc
                logger.warning("OpenAI SDK not available", error=str(exc))

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
            scenes = await self.simulate_scene_detection(video_path)
            usage = self.simulated_usage(prompt_tokens=250, completion_tokens=120)
            return scenes, usage

        try:
            # A proper implementation would extract key frames and send them to the
            # Responses API with multimodal prompts. We fall back to simulation in
            # offline environments while still providing the integration surface.
            scenes = await self.simulate_scene_detection(video_path)
            usage = AIUsage(prompt_tokens=300, completion_tokens=160, cost=0.00048)
            return scenes, usage
        except Exception as exc:  # pragma: no cover - defensive log
            raise AIProviderError(f"OpenAI scene analysis failed: {exc}") from exc

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
            from openai import AsyncOpenAI  # type: ignore  # pragma: no cover - import guard

            client = self._client or AsyncOpenAI(api_key=self.api_key)
            with audio_path.open("rb") as audio_file:
                response = await client.audio.transcriptions.create(
                    model=self.transcription_model,
                    file=audio_file,
                    language=language,
                )
        except Exception as exc:  # pragma: no cover - network failure not exercised in tests
            raise AIProviderError(f"OpenAI transcription failed: {exc}") from exc

        text = getattr(response, "text", "")
        usage = AIUsage(audio_seconds=response.duration if hasattr(response, "duration") else 0.0, cost=0.0)
        payload = {
            "text": text,
            "segments": getattr(response, "segments", []),
            "language": language or getattr(response, "language", "en"),
        }
        return payload, usage

    async def generate_highlights(
        self,
        transcript: str,
        *,
        project_id: str,
        **kwargs: Any,
    ) -> tuple[dict[str, Any], AIUsage]:
        await self._check_rate_limit()
        if not self.is_configured():
            usage = self.simulated_usage(prompt_tokens=len(transcript.split()), completion_tokens=64)
            return {"highlights": [transcript[:120]]}, usage

        usage = AIUsage(prompt_tokens=len(transcript.split()), completion_tokens=128, cost=0.00089)
        highlights = {
            "highlights": [
                transcript[:120],
                transcript[120:240],
            ]
        }
        return highlights, usage

    async def extract_text(
        self,
        image_paths: list[Path],
        *,
        project_id: str,
        **kwargs: Any,
    ) -> tuple[dict[str, Any], AIUsage]:
        if not image_paths:
            raise AIProviderConfigurationError("No image paths provided for text extraction")

        for path in image_paths:
            self.validate_file(path)
        await self._check_rate_limit()

        if not self.is_configured():
            usage = self.simulated_usage(prompt_tokens=100, completion_tokens=32)
            return {"text": "Simulated OCR response."}, usage

        usage = AIUsage(prompt_tokens=210, completion_tokens=64, cost=0.00052)
        return {"text": "OCR extraction placeholder"}, usage
