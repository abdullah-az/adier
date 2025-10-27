from __future__ import annotations

from pathlib import Path

import pytest

from app.repositories.provider_preference_repository import ProviderPreferenceRepository
from app.services.ai.base import AIProvider
from app.services.ai.exceptions import (
    AIProviderConfigurationError,
    AIProviderRateLimitError,
)
from app.services.ai.manager import AIManager
from app.services.ai.models import AICapability, AIUsage


class RateLimitedSceneProvider(AIProvider):
    name = "slow"
    display_name = "Slow Provider"
    capabilities = frozenset({AICapability.SCENE_ANALYSIS})

    def __init__(self) -> None:
        super().__init__(priority=10)

    async def analyze_scene(self, video_path: Path, *, project_id: str, **_: object):  # type: ignore[override]
        raise AIProviderRateLimitError("rate limited")


class SuccessfulSceneProvider(AIProvider):
    name = "success"
    display_name = "Successful Provider"
    capabilities = frozenset({AICapability.SCENE_ANALYSIS})

    def __init__(self) -> None:
        super().__init__(priority=20)

    async def analyze_scene(self, video_path: Path, *, project_id: str, **_: object):  # type: ignore[override]
        return ([{"timestamp": 0.0, "confidence": 0.99}], AIUsage(prompt_tokens=10, completion_tokens=5, cost=0.0002))


class TranscriptProvider(AIProvider):
    capabilities = frozenset({AICapability.TRANSCRIPTION})

    def __init__(self, name: str, transcript: str, priority: int = 100) -> None:
        self.name = name
        self.display_name = name.title()
        self._transcript = transcript
        super().__init__(priority=priority)

    async def transcribe_audio(self, audio_path: Path, *, project_id: str, language=None, **_: object):  # type: ignore[override]
        return (
            {
                "text": self._transcript,
                "segments": [],
                "language": language or "en",
            },
            AIUsage(completion_tokens=12, cost=0.0001),
        )


@pytest.mark.asyncio
async def test_scene_detection_fallback_uses_next_provider(tmp_path: Path) -> None:
    video = tmp_path / "demo.mp4"
    video.write_bytes(b"fake-video")

    manager = AIManager(settings=None, providers=[RateLimitedSceneProvider(), SuccessfulSceneProvider()])

    result = await manager.run_scene_detection("project", video)

    assert result["provider"]["name"] == "success"
    attempts = result["provider"]["attempts"]
    assert attempts[0]["status"] == "rate_limited"
    assert attempts[1]["status"] == "success"

    providers = await manager.list_providers()
    success_entry = next(item for item in providers if item["name"] == "success")
    assert success_entry["usage"]["requests"] == 1


@pytest.mark.asyncio
async def test_project_preferences_override_default(tmp_path: Path) -> None:
    audio = tmp_path / "audio.mp4"
    audio.write_bytes(b"fake-audio")

    repo = ProviderPreferenceRepository(tmp_path)
    primary = TranscriptProvider("primary", "primary transcript", priority=50)
    secondary = TranscriptProvider("secondary", "secondary transcript", priority=100)
    manager = AIManager(settings=None, preference_repository=repo, providers=[primary, secondary])

    await manager.set_preferences("project", {AICapability.TRANSCRIPTION.value: "secondary"})

    result = await manager.run_transcription("project", audio)
    assert result["provider"]["name"] == "secondary"
    assert result["text"] == "secondary transcript"


@pytest.mark.asyncio
async def test_invalid_preference_rejected(tmp_path: Path) -> None:
    repo = ProviderPreferenceRepository(tmp_path)
    manager = AIManager(settings=None, preference_repository=repo, providers=[SuccessfulSceneProvider()])

    with pytest.raises(AIProviderConfigurationError):
        await manager.set_preferences("project", {AICapability.TRANSCRIPTION.value: "missing"})

    # Ensure valid capability with misconfigured provider raises as well
    with pytest.raises(AIProviderConfigurationError):
        await manager.set_preferences("project", {"unknown": "success"})
