from __future__ import annotations

import sqlite3
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque

import pytest
from fastapi.testclient import TestClient

from app.core import config
from app.repositories.job_repository import JobRepository
from app.repositories.video_repository import VideoAssetRepository
from app.services.job_service import JobService
from app.services.video_pipeline_service import VideoPipelineService
from app.utils.storage import StorageManager

_SAMPLE_MP4_BYTES = (
    b"\x00\x00\x00\x18ftypmp42"
    b"\x00\x00\x00\x00mp42mp41"
    b"\x00\x00\x00\x08free"
    b"\x00\x00\x00\x0cmdat"
    b"\x00\x00\x00\x00"
)

_SAMPLE_MP3_BYTES = (
    b"ID3\x03\x00\x00\x00\x00\x00\x15"
    b"TIT2\x00\x00\x00\x05\x00\x03Test"
    b"\x00\x00"
)


class DummyQueue:
    """Lightweight queue used for API integration tests."""

    def __init__(self) -> None:
        self.enqueued: Deque[str] = deque()

    async def enqueue(self, job_id: str) -> None:
        self.enqueued.append(job_id)

    async def schedule_retry(self, job_id: str, delay: float) -> None:
        # Tests rely on the retry path being observable without background tasks.
        self.enqueued.append(job_id)


@dataclass
class DummyRuntime:
    job_service: JobService
    job_queue: DummyQueue
    storage_manager: StorageManager
    video_repository: VideoAssetRepository
    pipeline_service: VideoPipelineService

    async def start(self) -> None:  # pragma: no cover - intentionally empty for tests
        return None

    async def stop(self) -> None:  # pragma: no cover - intentionally empty for tests
        return None


@pytest.fixture
def temp_storage_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("storage")


@pytest.fixture
def test_settings(temp_storage_dir: Path, monkeypatch: pytest.MonkeyPatch):
    config.get_settings.cache_clear()
    settings = config.Settings(
        storage_path=str(temp_storage_dir),
        log_file=None,
        debug=True,
        worker_concurrency=1,
        max_queue_size=16,
        job_retry_delay_seconds=0.0,
    )
    monkeypatch.setattr(config, "get_settings", lambda: settings)
    monkeypatch.setattr("app.main.get_settings", lambda: settings)
    monkeypatch.setattr("app.api.dependencies.get_settings", lambda: settings)
    yield settings
    config.get_settings.cache_clear()


@pytest.fixture(autouse=True)
def stub_storage_ffmpeg(monkeypatch: pytest.MonkeyPatch):
    async def _metadata_stub(path: Path | str) -> dict:
        file_path = Path(path)
        size_bytes = file_path.stat().st_size if file_path.exists() else 0
        return {
            "duration": 1.0,
            "width": 1920,
            "height": 1080,
            "codec": "h264",
            "fps": 30.0,
            "bitrate": 512000,
            "size_bytes": size_bytes,
            "has_audio": True,
            "audio_codec": "aac",
            "audio_channels": 2,
            "audio_sample_rate": 44100,
        }

    async def _thumbnail_stub(video_path: Path | str, thumbnail_path: Path | str, **_: object) -> Path:
        output_path = Path(thumbnail_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"thumbnail")
        return output_path

    monkeypatch.setattr("app.services.storage_service.get_video_metadata", _metadata_stub)
    monkeypatch.setattr("app.services.storage_service.extract_thumbnail", _thumbnail_stub)


@pytest.fixture
def sample_video_bytes() -> bytes:
    return _SAMPLE_MP4_BYTES


@pytest.fixture
def sample_audio_bytes() -> bytes:
    return _SAMPLE_MP3_BYTES


@pytest.fixture
def sample_video_file(tmp_path: Path, sample_video_bytes: bytes) -> Path:
    path = tmp_path / "sample.mp4"
    path.write_bytes(sample_video_bytes)
    return path


@pytest.fixture
def sample_audio_file(tmp_path: Path, sample_audio_bytes: bytes) -> Path:
    path = tmp_path / "sample.mp3"
    path.write_bytes(sample_audio_bytes)
    return path


@pytest.fixture
def sqlite_connection(tmp_path: Path):
    db_path = tmp_path / "test.db"
    connection = sqlite3.connect(db_path)
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture
def sqlite_url(sqlite_connection: sqlite3.Connection, tmp_path: Path) -> str:
    return f"sqlite:///{tmp_path / 'test.db'}"


@pytest.fixture
def api_client(test_settings, monkeypatch: pytest.MonkeyPatch):
    storage_manager = StorageManager(test_settings.storage_path)
    video_repository = VideoAssetRepository(test_settings.storage_path)
    job_repository = JobRepository(test_settings.storage_path)
    job_service = JobService(
        job_repository,
        default_max_attempts=test_settings.job_max_attempts,
        default_retry_delay=test_settings.job_retry_delay_seconds,
    )
    queue = DummyQueue()
    job_service.attach_queue(queue)

    pipeline_service = VideoPipelineService(
        storage_manager=storage_manager,
        video_repository=video_repository,
        settings=test_settings,
    )

    runtime = DummyRuntime(
        job_service=job_service,
        job_queue=queue,
        storage_manager=storage_manager,
        video_repository=video_repository,
        pipeline_service=pipeline_service,
    )

    monkeypatch.setattr("app.main.create_worker_runtime", lambda _: runtime)

    from app.main import create_app

    app = create_app()

    with TestClient(app) as client:
        yield client, runtime
