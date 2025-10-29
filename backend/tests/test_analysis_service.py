from __future__ import annotations

import json
from collections import deque
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.models.base import Base
from backend.app.models.enums import MediaAssetType
from backend.app.models.media_asset import MediaAsset
from backend.app.repositories.media_asset import MediaAssetRepository
from backend.app.services.ai import (
    AllProvidersFailedError,
    AnalysisService,
    AnalysisServiceError,
    ProviderErrorInfo,
    ProviderResponse,
    SceneInput,
    TranscriptSegment,
    VideoAnalysisResult,
)


@pytest.fixture()
def db_session(tmp_path: Path) -> Session:
    engine = create_engine(f"sqlite:///{tmp_path / 'analysis.db'}")
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    try:
        with TestingSession() as session:
            yield session
    finally:
        engine.dispose()


class DummyRouter:
    def __init__(self, responses: deque[ProviderResponse]) -> None:
        self._responses = responses
        self.calls = 0
        self.last_prompt: str | None = None

    def generate_text(self, *, prompt: str, **_: object) -> ProviderResponse:
        self.calls += 1
        self.last_prompt = prompt
        if not self._responses:
            raise RuntimeError("No provider responses remaining")
        return self._responses.popleft()


class FailingRouter:
    def generate_text(self, *, prompt: str, **_: object) -> ProviderResponse:
        raise AllProvidersFailedError(
            [ProviderErrorInfo(provider="mock", message="temporary failure", retryable=True)]
        )


def _create_asset(session: Session) -> MediaAsset:
    asset = MediaAsset(
        id="asset-1",
        project_id="project-1",
        type=MediaAssetType.SOURCE,
        filename="source.mp4",
        file_path="project-1/source/source.mp4",
    )
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return asset


def test_analysis_service_produces_structured_result_and_caches(db_session: Session) -> None:
    asset = _create_asset(db_session)
    repository = MediaAssetRepository(db_session)

    transcript = [
        TranscriptSegment(start=0.0, end=8.5, text="Welcome to our cardio warmup."),
        TranscriptSegment(start=8.5, end=20.0, text="Instructor Alex demonstrates HIIT movements."),
    ]
    scenes = [
        SceneInput(
            scene_id="scene-1",
            start=0.0,
            end=8.5,
            transcript="Introductory greetings about cardio health.",
            sentiment=0.0,
            visual_intensity=0.3,
            tags=["intro"],
        ),
        SceneInput(
            scene_id="scene-2",
            start=8.5,
            end=20.0,
            transcript="Alex leads high intensity interval training with jumps and squats.",
            sentiment=0.8,
            visual_intensity=0.9,
            tags=["training", "cardio"],
        ),
    ]

    provider_payload = {
        "topics": ["cardio training", "HIIT"],
        "summary": "The video covers a cardio-focused HIIT routine led by Alex.",
        "entities": [
            {
                "name": "Alex",
                "type": "person",
                "mentions": ["Instructor Alex"],
                "salience": 0.92,
            }
        ],
        "moments": [
            {
                "scene_id": "scene-2",
                "description": "Alex demonstrates the HIIT sequence",
                "reasons": ["High energy", "Clear instructions"],
            }
        ],
    }

    router = DummyRouter(deque([ProviderResponse(provider="mock", content=json.dumps(provider_payload))]))
    service = AnalysisService(router=router, repository=repository)

    result = service.analyse_media_asset(asset=asset, transcript_segments=transcript, scenes=scenes)

    assert isinstance(result, VideoAnalysisResult)
    assert result.topics == provider_payload["topics"]
    assert result.entities[0].name == "Alex"
    assert result.key_moments[0].scene_id == "scene-2"
    assert result.scene_scores[1].highlight_score >= result.scene_scores[0].highlight_score
    assert router.last_prompt and "Scene scene-1" in router.last_prompt
    assert asset.analysis_cache is not None
    assert router.calls == 1

    cached_result = service.analyse_media_asset(asset=asset, transcript_segments=transcript, scenes=scenes)
    assert router.calls == 1  # no additional provider call
    assert cached_result.model_dump() == result.model_dump()


def test_analysis_service_surfaces_provider_errors(db_session: Session) -> None:
    asset = _create_asset(db_session)
    repository = MediaAssetRepository(db_session)
    service = AnalysisService(router=FailingRouter(), repository=repository)

    transcript = [TranscriptSegment(start=0.0, end=5.0, text="Brief clip.")]
    scenes = [
        SceneInput(
            scene_id="scene-1",
            start=0.0,
            end=5.0,
            transcript="Scene text",
            sentiment=0.1,
            visual_intensity=0.4,
        )
    ]

    with pytest.raises(AnalysisServiceError) as exc:
        service.analyse_media_asset(asset=asset, transcript_segments=transcript, scenes=scenes)

    assert exc.value.retryable is True
    assert "mock" in str(exc.value)
    assert asset.analysis_cache is None
