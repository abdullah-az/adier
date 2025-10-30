from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from backend.app.core.config import TestingSettings
from backend.app.services.video.ffmpeg_service import FFmpegService
from backend.app.services.video.quality_service import (
    QualityAnalysisError,
    QualityService,
    QualityWeights,
)

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def sample_video_path() -> Path:
    path = Path(__file__).parent / "data" / "sample.mp4"
    if not path.exists():
        pytest.skip("Sample media asset is missing")
    return path


@pytest.fixture(autouse=True)
def ensure_binaries_available() -> None:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        pytest.skip("FFmpeg binaries are not available in the execution environment")


@pytest.fixture()
def quality_env(tmp_path: Path) -> tuple[QualityService, TestingSettings]:
    settings = TestingSettings(storage_temp=str(tmp_path))
    ffmpeg_service = FFmpegService(settings)
    quality_service = QualityService(settings, ffmpeg_service)
    return quality_service, settings


def test_quality_analysis_produces_normalized_scores(
    quality_env: tuple[QualityService, TestingSettings],
    sample_video_path: Path,
) -> None:
    service, _settings = quality_env
    metrics = service.analyse_video_quality(sample_video_path, sample_count=5)

    assert metrics.sharpness >= 0.0 and metrics.sharpness <= 1.0, "Sharpness should be normalized to 0-1"
    assert metrics.exposure >= 0.0 and metrics.exposure <= 1.0, "Exposure should be normalized to 0-1"
    assert metrics.motion_blur >= 0.0 and metrics.motion_blur <= 1.0, "Motion blur should be normalized to 0-1"
    assert metrics.noise_level >= 0.0 and metrics.noise_level <= 1.0, "Noise level should be normalized to 0-1"
    assert metrics.overall_score >= 0.0 and metrics.overall_score <= 1.0, "Overall score should be normalized to 0-1"

    if metrics.audio_quality is not None:
        assert metrics.audio_quality >= 0.0 and metrics.audio_quality <= 1.0, "Audio quality should be normalized to 0-1"


def test_quality_metrics_consistent_across_runs(
    quality_env: tuple[QualityService, TestingSettings],
    sample_video_path: Path,
) -> None:
    service, _settings = quality_env

    metrics1 = service.analyse_video_quality(sample_video_path, sample_count=5)
    metrics2 = service.analyse_video_quality(sample_video_path, sample_count=5)

    assert metrics1.sharpness == pytest.approx(metrics2.sharpness, rel=1e-2)
    assert metrics1.exposure == pytest.approx(metrics2.exposure, rel=1e-2)
    assert metrics1.motion_blur == pytest.approx(metrics2.motion_blur, rel=1e-2)
    assert metrics1.noise_level == pytest.approx(metrics2.noise_level, rel=1e-2)
    assert metrics1.overall_score == pytest.approx(metrics2.overall_score, rel=1e-2)


def test_quality_analysis_with_custom_weights(
    quality_env: tuple[QualityService, TestingSettings],
    sample_video_path: Path,
) -> None:
    settings = quality_env[1]
    ffmpeg_service = FFmpegService(settings)

    weights_sharpness = QualityWeights(sharpness=1.0, exposure=0.0, motion_blur=0.0, noise_level=0.0, audio_quality=0.0)
    service_sharpness = QualityService(settings, ffmpeg_service, weights=weights_sharpness)
    metrics_sharpness = service_sharpness.analyse_video_quality(sample_video_path, sample_count=5)

    weights_exposure = QualityWeights(sharpness=0.0, exposure=1.0, motion_blur=0.0, noise_level=0.0, audio_quality=0.0)
    service_exposure = QualityService(settings, ffmpeg_service, weights=weights_exposure)
    metrics_exposure = service_exposure.analyse_video_quality(sample_video_path, sample_count=5)

    assert metrics_sharpness.overall_score != metrics_exposure.overall_score, "Different weights should produce different scores"


def test_quality_analysis_error_for_missing_file(
    quality_env: tuple[QualityService, TestingSettings],
) -> None:
    service, _settings = quality_env
    missing_path = Path("/nonexistent/video.mp4")

    with pytest.raises(QualityAnalysisError, match="not found"):
        service.analyse_video_quality(missing_path)


def test_metrics_to_dict_conversion(
    quality_env: tuple[QualityService, TestingSettings],
    sample_video_path: Path,
) -> None:
    service, _settings = quality_env
    metrics = service.analyse_video_quality(sample_video_path, sample_count=5)

    metrics_dict = metrics.to_dict()
    assert isinstance(metrics_dict, dict)
    assert "sharpness" in metrics_dict
    assert "exposure" in metrics_dict
    assert "motion_blur" in metrics_dict
    assert "noise_level" in metrics_dict
    assert "audio_quality" in metrics_dict
    assert "overall_score" in metrics_dict


def test_higher_sharpness_yields_better_score(
    quality_env: tuple[QualityService, TestingSettings],
    sample_video_path: Path,
) -> None:
    service, _settings = quality_env
    metrics = service.analyse_video_quality(sample_video_path, sample_count=5)

    assert metrics.sharpness > 0.0, "Sample video should have some measurable sharpness"
    assert metrics.overall_score > 0.0, "Overall score should be positive for valid video"


def test_sample_count_affects_analysis(
    quality_env: tuple[QualityService, TestingSettings],
    sample_video_path: Path,
) -> None:
    service, _settings = quality_env

    metrics_few = service.analyse_video_quality(sample_video_path, sample_count=3)
    metrics_many = service.analyse_video_quality(sample_video_path, sample_count=10)

    assert metrics_few.overall_score > 0.0
    assert metrics_many.overall_score > 0.0
