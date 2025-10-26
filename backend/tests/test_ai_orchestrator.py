from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Iterable

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.api.dependencies import get_ai_orchestrator
from app.api.providers import router as providers_router
from app.repositories.provider_repository import ProviderConfigRepository
from app.services.ai import (
    AIOrchestrator,
    LocalFallbackProvider,
    ProviderInvocationError,
    ProviderRateLimitError,
    ProviderResult,
    ProviderTask,
    ProviderUnavailableError,
)


class DummyProvider(LocalFallbackProvider):
    """Customisable provider implementation for tests."""

    def __init__(
        self,
        provider_id: str,
        *,
        supports: Iterable[ProviderTask] | None = None,
        configured: bool = True,
        scene_result: ProviderResult | None = None,
        transcription_result: ProviderResult | None = None,
        highlight_result: ProviderResult | None = None,
        text_result: ProviderResult | None = None,
        fail_on: dict[str, Exception] | None = None,
    ) -> None:
        super().__init__()
        self.provider_id = provider_id
        self.display_name = provider_id.title()
        self.capabilities = frozenset(supports or {
            ProviderTask.SCENE_ANALYSIS,
            ProviderTask.TRANSCRIPTION,
            ProviderTask.HIGHLIGHT_GENERATION,
            ProviderTask.TEXT_EXTRACTION,
        })
        self._configured = configured
        self._scene_result = scene_result or ProviderResult(data={"scenes": [{"timestamp": 0, "confidence": 0.9}]})
        self._transcription_result = transcription_result or ProviderResult(data={"transcript": "ok", "language": "en"})
        self._highlight_result = highlight_result or ProviderResult(data={"highlights": ["Highlight"]})
        self._text_result = text_result or ProviderResult(data={"text": "Sample"})
        self._fail_on = fail_on or {}

    async def analyze_scene(self, *, video_frames: list[Any], transcript: str | None = None, **kwargs: Any) -> ProviderResult:
        failure = self._fail_on.get("analyze_scene")
        if failure:
            raise failure
        return self._scene_result

    async def transcribe_audio(self, *, audio_source: Any, language: str | None = None, **kwargs: Any) -> ProviderResult:
        failure = self._fail_on.get("transcribe_audio")
        if failure:
            raise failure
        return self._transcription_result

    async def generate_highlights(self, *, transcript: str, metadata: dict[str, Any] | None = None, **kwargs: Any) -> ProviderResult:
        failure = self._fail_on.get("generate_highlights")
        if failure:
            raise failure
        return self._highlight_result

    async def extract_text(self, *, document: Any, **kwargs: Any) -> ProviderResult:
        failure = self._fail_on.get("extract_text")
        if failure:
            raise failure
        return self._text_result


@pytest.fixture()
def settings(tmp_path) -> SimpleNamespace:
    return SimpleNamespace(
        ai_provider_priority="primary,secondary",
        ai_cost_currency="USD",
        storage_path=str(tmp_path),
    )


@pytest.fixture()
def provider_repository(tmp_path) -> ProviderConfigRepository:
    return ProviderConfigRepository(tmp_path)


@pytest.fixture()
async def orchestrator(settings: SimpleNamespace, provider_repository: ProviderConfigRepository) -> AIOrchestrator:
    primary = DummyProvider("primary")
    secondary = DummyProvider("secondary")
    orch = await AIOrchestrator.create(
        settings,
        provider_repository,
        providers=[primary, secondary],
        fallback_provider=LocalFallbackProvider(),
    )
    return orch


@pytest.mark.asyncio
async def test_orchestrator_fallback_to_next_provider(settings, provider_repository):
    primary = DummyProvider(
        "primary",
        fail_on={"analyze_scene": ProviderRateLimitError("throttled")},
    )
    secondary_result = ProviderResult(data={"scenes": [{"timestamp": 5, "confidence": 0.95}]}, cost=0.2)
    secondary = DummyProvider("secondary", scene_result=secondary_result)

    orch = await AIOrchestrator.create(
        settings,
        provider_repository,
        providers=[primary, secondary],
        fallback_provider=LocalFallbackProvider(),
    )

    invocation = await orch.analyze_scene("project-1", video_frames=["frame"])
    assert invocation.provider_id == "secondary"
    payload = invocation.to_dict()
    assert payload["result"]["scenes"][0]["timestamp"] == 5
    assert payload["metadata"]["attempts"][0]["status"] == "rate_limited"
    summary = orch.get_usage_summary()
    assert summary["secondary"]["requests"] == 1
    assert "primary" in summary  # recorded even with no success


@pytest.mark.asyncio
async def test_project_override_changes_priority(orchestrator: AIOrchestrator):
    overrides = await orchestrator.set_project_overrides("demo", priority=["secondary"])
    assert overrides["priority"][0] == "secondary"

    invocation = await orchestrator.analyze_scene("demo", video_frames=[])
    assert invocation.provider_id == "secondary"


@pytest.mark.asyncio
async def test_all_providers_failed_raises(settings, provider_repository):
    primary = DummyProvider(
        "primary",
        fail_on={"transcribe_audio": ProviderInvocationError("boom")},
    )
    secondary = DummyProvider("secondary", configured=False)
    orch = await AIOrchestrator.create(
        settings,
        provider_repository,
        providers=[primary, secondary],
        fallback_provider=DummyProvider(
            "local-fallback",
            supports={ProviderTask.TRANSCRIPTION},
            configured=False,
        ),
    )

    with pytest.raises(ProviderUnavailableError) as exc:
        await orch.transcribe_audio("p", audio_source=b"123")
    assert exc.value.attempts[-1]["status"] in {"unavailable", "not_configured"}


@pytest.mark.asyncio
async def test_provider_api_listing(settings, provider_repository):
    primary = DummyProvider(
        "primary",
        scene_result=ProviderResult(data={"scenes": [{"timestamp": 0, "confidence": 0.5}]}, cost=0.1),
    )
    secondary = DummyProvider("secondary")
    orch = await AIOrchestrator.create(
        settings,
        provider_repository,
        providers=[primary, secondary],
        fallback_provider=LocalFallbackProvider(),
    )

    app = FastAPI()
    app.include_router(providers_router)
    app.dependency_overrides[get_ai_orchestrator] = lambda: orch

    async with AsyncClient(app=app, base_url="http://test") as client:
        list_response = await client.get("/providers")
        assert list_response.status_code == 200
        payload = list_response.json()
        provider_ids = {entry["id"] for entry in payload["providers"]}
        assert {"primary", "secondary", "local"}.issubset(provider_ids)

        update_response = await client.put("/providers/priority", json={"priority": ["secondary", "primary"]})
        assert update_response.status_code == 200
        assert update_response.json()["priority"][0] == "secondary"

        project_update = await client.put(
            "/providers/projects/demo",
            json={"priority": ["primary"], "task_overrides": {"transcription": ["secondary"]}},
        )
        assert project_update.status_code == 200
        body = project_update.json()
        assert body["task_overrides"]["transcription"][0] == "secondary"

        usage_response = await client.get("/providers/usage")
        assert usage_response.status_code == 200
        usage_payload = usage_response.json()
        assert "providers" in usage_payload
