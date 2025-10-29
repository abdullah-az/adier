from __future__ import annotations

from unittest.mock import MagicMock, Mock

import pytest

from backend.app.models.clip import Clip, ClipVersion
from backend.app.models.enums import ClipStatus, ClipVersionStatus
from backend.app.repositories.clip import ClipVersionRepository
from backend.app.services.ai.analysis_service import SceneScore
from backend.app.services.video.ranking_service import RankingService, RankingWeights


@pytest.fixture()
def mock_repository() -> ClipVersionRepository:
    mock = MagicMock(spec=ClipVersionRepository)
    return mock


@pytest.fixture()
def sample_clip_versions() -> list[ClipVersion]:
    versions = []

    for i in range(5):
        clip = Clip(
            id=f"clip-{i}",
            project_id="project-1",
            title=f"Clip {i}",
            status=ClipStatus.DRAFT,
            start_time=float(i * 10),
            end_time=float((i + 1) * 10),
        )

        version = ClipVersion(
            id=f"version-{i}",
            clip_id=f"clip-{i}",
            version_number=1,
            status=ClipVersionStatus.DRAFT,
            quality_metrics={
                "sharpness": 0.8 - (i * 0.1),
                "exposure": 0.7 - (i * 0.05),
                "motion_blur": 0.2 + (i * 0.1),
                "noise_level": 0.9 - (i * 0.1),
                "audio_quality": 0.85 - (i * 0.1),
                "overall_score": 0.8 - (i * 0.15),
            },
        )
        version.clip = clip
        versions.append(version)

    return versions


@pytest.fixture()
def sample_scene_scores() -> dict[str, SceneScore]:
    return {
        "scene_0": SceneScore(scene_id="scene_0", start=0.0, end=10.0, semantic=0.9, sentiment=0.8, visual=0.7, highlight_score=0.85),
        "scene_10": SceneScore(scene_id="scene_10", start=10.0, end=20.0, semantic=0.7, sentiment=0.6, visual=0.5, highlight_score=0.65),
        "scene_20": SceneScore(scene_id="scene_20", start=20.0, end=30.0, semantic=0.6, sentiment=0.5, visual=0.4, highlight_score=0.55),
        "scene_30": SceneScore(scene_id="scene_30", start=30.0, end=40.0, semantic=0.5, sentiment=0.4, visual=0.3, highlight_score=0.45),
        "scene_40": SceneScore(scene_id="scene_40", start=40.0, end=50.0, semantic=0.4, sentiment=0.3, visual=0.2, highlight_score=0.35),
    }


def test_rank_clips_orders_by_quality_score(
    mock_repository: ClipVersionRepository,
    sample_clip_versions: list[ClipVersion],
) -> None:
    service = RankingService(mock_repository)
    rankings = service.rank_clips(sample_clip_versions)

    assert len(rankings) == 5
    assert rankings[0].quality_score >= rankings[1].quality_score
    assert rankings[1].quality_score >= rankings[2].quality_score
    assert rankings[2].quality_score >= rankings[3].quality_score
    assert rankings[3].quality_score >= rankings[4].quality_score


def test_rank_clips_combines_quality_and_ai_scores(
    mock_repository: ClipVersionRepository,
    sample_clip_versions: list[ClipVersion],
    sample_scene_scores: dict[str, SceneScore],
) -> None:
    service = RankingService(mock_repository, weights=RankingWeights(quality=0.5, ai_score=0.5))
    rankings = service.rank_clips(sample_clip_versions, scene_scores=sample_scene_scores)

    assert len(rankings) == 5

    for ranking in rankings:
        assert ranking.combined_score >= 0.0 and ranking.combined_score <= 1.0


def test_get_top_clips_returns_limited_results(
    mock_repository: ClipVersionRepository,
    sample_clip_versions: list[ClipVersion],
) -> None:
    service = RankingService(mock_repository)
    top_3 = service.get_top_clips(sample_clip_versions, top_n=3)

    assert len(top_3) == 3
    assert top_3[0].combined_score >= top_3[1].combined_score
    assert top_3[1].combined_score >= top_3[2].combined_score


def test_suggest_retakes_identifies_low_quality_clips(
    mock_repository: ClipVersionRepository,
    sample_clip_versions: list[ClipVersion],
) -> None:
    service = RankingService(mock_repository, quality_threshold=0.6)
    suggestions = service.suggest_retakes(sample_clip_versions)

    assert len(suggestions) >= 1

    for suggestion in suggestions:
        assert suggestion.quality_score < 0.6
        assert len(suggestion.issues) > 0


def test_suggest_retakes_with_custom_threshold(
    mock_repository: ClipVersionRepository,
    sample_clip_versions: list[ClipVersion],
) -> None:
    service = RankingService(mock_repository)
    suggestions = service.suggest_retakes(sample_clip_versions, quality_threshold=0.9)

    assert len(suggestions) >= 4


def test_ranking_weights_normalization() -> None:
    weights = RankingWeights(quality=3.0, ai_score=1.0)
    normalized = weights.normalised()

    assert normalized[0] == pytest.approx(0.75)
    assert normalized[1] == pytest.approx(0.25)
    assert sum(normalized) == pytest.approx(1.0)


def test_zero_weights_defaults_to_quality_only() -> None:
    weights = RankingWeights(quality=0.0, ai_score=0.0)
    normalized = weights.normalised()

    assert normalized[0] == 1.0
    assert normalized[1] == 0.0


def test_ranking_generates_recommendations(
    mock_repository: ClipVersionRepository,
    sample_clip_versions: list[ClipVersion],
) -> None:
    service = RankingService(mock_repository)
    rankings = service.rank_clips(sample_clip_versions)

    for ranking in rankings:
        assert ranking.recommendation in [
            "Excellent - Ready for publication",
            "Good - Minor improvements possible",
            "Fair - Consider improvements",
            "Poor - Retake recommended",
        ]


def test_retake_suggestions_identify_specific_issues(
    mock_repository: ClipVersionRepository,
) -> None:
    clip = Clip(
        id="clip-poor",
        project_id="project-1",
        title="Poor Quality Clip",
        status=ClipStatus.DRAFT,
    )

    version = ClipVersion(
        id="version-poor",
        clip_id="clip-poor",
        version_number=1,
        status=ClipVersionStatus.DRAFT,
        quality_metrics={
            "sharpness": 0.3,
            "exposure": 0.4,
            "motion_blur": 0.7,
            "noise_level": 0.3,
            "audio_quality": 0.2,
            "overall_score": 0.3,
        },
    )
    version.clip = clip

    service = RankingService(mock_repository)
    suggestions = service.suggest_retakes([version], quality_threshold=0.5)

    assert len(suggestions) == 1
    assert len(suggestions[0].issues) >= 4


def test_ranking_preserves_quality_metrics(
    mock_repository: ClipVersionRepository,
    sample_clip_versions: list[ClipVersion],
) -> None:
    service = RankingService(mock_repository)
    rankings = service.rank_clips(sample_clip_versions)

    for ranking in rankings:
        assert ranking.quality_metrics is not None
        assert "overall_score" in ranking.quality_metrics
        assert "sharpness" in ranking.quality_metrics


def test_ranking_handles_missing_quality_metrics(
    mock_repository: ClipVersionRepository,
) -> None:
    clip = Clip(
        id="clip-no-metrics",
        project_id="project-1",
        title="No Metrics Clip",
        status=ClipStatus.DRAFT,
    )

    version = ClipVersion(
        id="version-no-metrics",
        clip_id="clip-no-metrics",
        version_number=1,
        status=ClipVersionStatus.DRAFT,
        quality_metrics=None,
    )
    version.clip = clip

    service = RankingService(mock_repository)
    rankings = service.rank_clips([version])

    assert len(rankings) == 1
    assert rankings[0].quality_score == 0.0
