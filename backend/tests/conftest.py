from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api import dependencies as api_dependencies
from app.core import config as core_config
from app.main import create_app


@pytest.fixture()
def storage_root(tmp_path: Path) -> Path:
    storage_path = tmp_path / "storage"
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path


@pytest.fixture()
def settings_override(monkeypatch: pytest.MonkeyPatch, storage_root: Path, tmp_path: Path):
    """Provide Settings instance backed by per-test storage and SQLite database."""

    database_path = tmp_path / "app.db"
    monkeypatch.setenv("STORAGE_PATH", str(storage_root))
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{database_path}")
    monkeypatch.setenv("WORKER_CONCURRENCY", "2")
    monkeypatch.setenv("MAX_QUEUE_SIZE", "8")

    core_config.get_settings.cache_clear()
    api_dependencies._storage_manager_factory.cache_clear()
    api_dependencies._video_repository_factory.cache_clear()
    api_dependencies._job_repository_factory.cache_clear()

    settings = core_config.get_settings()
    yield settings

    core_config.get_settings.cache_clear()
    api_dependencies._storage_manager_factory.cache_clear()
    api_dependencies._video_repository_factory.cache_clear()
    api_dependencies._job_repository_factory.cache_clear()


@pytest.fixture(autouse=True)
def stub_ffmpeg_operations(monkeypatch: pytest.MonkeyPatch):
    """Avoid invoking real FFmpeg operations during tests."""

    async def fake_metadata(path: Path) -> dict[str, Any]:
        size_bytes = path.stat().st_size if path.exists() else 0
        return {
            "duration": 1.0,
            "width": 1280,
            "height": 720,
            "codec": "h264",
            "fps": 30.0,
            "bitrate": 5_000_000,
            "size_bytes": size_bytes,
            "has_audio": True,
            "audio_codec": "aac",
            "audio_channels": 2,
            "audio_sample_rate": 48_000,
        }

    async def fake_thumbnail(video_path: Path, thumbnail_path: Path, **_: Any) -> Path:
        thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
        thumbnail_path.write_bytes(b"thumbnail-bytes")
        return thumbnail_path

    monkeypatch.setattr("app.services.storage_service.get_video_metadata", fake_metadata)
    monkeypatch.setattr("app.services.storage_service.extract_thumbnail", fake_thumbnail)


@pytest.fixture()
def test_app(settings_override) -> Any:
    """Instantiate a FastAPI app wired to ephemeral resources."""

    return create_app()


@pytest.fixture()
def client(test_app, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Provide TestClient with accelerated worker handlers for integration tests."""

    monkeypatch.setattr("app.workers.handlers._STEP_DELAY_SECONDS", 0.0)
    with TestClient(test_app) as http_client:
        yield http_client


@pytest.fixture()
def sample_video_path() -> Path:
    return Path(__file__).parent / "fixtures" / "sample_video.mp4"


@pytest.fixture()
def sample_video_bytes(sample_video_path: Path) -> bytes:
    return sample_video_path.read_bytes()
