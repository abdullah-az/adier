from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from app.services.ai.base import AIProvider, LocalSimulationMixin
from app.services.ai.models import AICapability, AIUsage


class LocalWhisperProvider(LocalSimulationMixin, AIProvider):
    """Fallback provider that uses whisper.cpp binaries when available.

    In environments without the binary the provider falls back to lightweight
    simulations so that higher-level orchestration and testing continue to
    function deterministically.
    """

    name = "local"
    display_name = "Local Whisper"
    capabilities = frozenset({AICapability.TRANSCRIPTION, AICapability.SCENE_ANALYSIS})

    def __init__(
        self,
        *,
        whisper_binary: Optional[Path] = None,
        model_path: Optional[Path] = None,
        priority: int = 1000,
        rate_limit_per_minute: Optional[float] = None,
    ) -> None:
        super().__init__(priority=priority, rate_limit_per_minute=rate_limit_per_minute)
        self.whisper_binary = whisper_binary
        self.model_path = model_path

    def is_configured(self) -> bool:
        return True

    def has_whisper_binary(self) -> bool:
        return self.whisper_binary is not None and self.whisper_binary.exists()

    async def analyze_scene(
        self,
        video_path: Path,
        *,
        project_id: str,
        **kwargs: Any,
    ) -> tuple[list[dict[str, Any]], AIUsage]:
        self.validate_file(video_path)
        await self._check_rate_limit()
        scenes = await self.simulate_scene_detection(video_path, score=0.8)
        usage = self.simulated_usage(prompt_tokens=50, completion_tokens=10)
        return scenes, usage

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

        if self.has_whisper_binary():
            try:
                result = await self._run_whisper(audio_path, language=language)
                return result, AIUsage(audio_seconds=result.get("segments", [{}])[0].get("end", 0.0), cost=0.0)
            except Exception as exc:  # pragma: no cover - whisper binary failure
                logger.warning("Local whisper execution failed, falling back to simulation", error=str(exc))

        transcription = await self.simulate_transcription(audio_path, language=language)
        usage = self.simulated_usage(audio_seconds=transcription.get("segments", [{}])[0].get("end", 0.0))
        return transcription, usage

    async def _run_whisper(self, audio_path: Path, *, language: Optional[str]) -> dict[str, Any]:
        if not self.has_whisper_binary():
            raise RuntimeError("whisper.cpp binary not configured")
        command = [str(self.whisper_binary), "-f", str(audio_path)]
        if self.model_path:
            command.extend(["-m", str(self.model_path)])
        if language:
            command.extend(["-l", language])

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(stderr.decode("utf-8", errors="ignore"))

        transcript = stdout.decode("utf-8", errors="ignore").strip()
        if not transcript:
            transcript = ""
        return {
            "text": transcript,
            "segments": [
                {
                    "text": transcript,
                    "start": 0.0,
                    "end": 0.0,
                    "confidence": 0.5,
                }
            ],
            "language": language or "en",
        }
