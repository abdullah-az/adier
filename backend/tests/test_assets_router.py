from __future__ import annotations

import io
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import TestingSettings
from backend.app.main import create_app
from backend.app.models.base import Base
from backend.app.models.media_asset import MediaAsset
from backend.app.models.project import Project
from backend.app.models.enums import MediaAssetType, ProcessingJobStatus, ProjectStatus
from backend.app.repositories.media_asset import MediaAssetRepository
from backend.app.services.storage_service import StorageService
from backend.app.workers.job_manager import ProcessingJobLifecycle


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


@pytest.fixture()
def settings(tmp_path) -> TestingSettings:
    storage_root = tmp_path / "storage"
    storage_temp = tmp_path / "temp"
    return TestingSettings(
        storage_root=str(storage_root),
        storage_temp=str(storage_temp),
        database_url="sqlite:///:memory:",
    )


@pytest.fixture()
def client(db_session: Session, settings: TestingSettings) -> TestClient:
    app = create_app()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    from backend.app.core.database import get_db
    from backend.app.core.config import get_settings

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = lambda: settings

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_upload_asset_creates_media_asset_and_job(
    client: TestClient,
    db_session: Session,
    settings: TestingSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = Project(id="proj-123", name="Upload Project", status=ProjectStatus.ACTIVE)
    db_session.add(project)
    db_session.commit()

    created_jobs: list[dict[str, object]] = []

    def fake_enqueue(
        cls,
        *,
        job_type,
        payload,
        clip_version_id=None,
        priority=0,
        queue_name=None,
    ):
        created_jobs.append({
            "job_type": job_type,
            "payload": payload,
            "priority": priority,
            "queue": queue_name,
        })
        return SimpleNamespace(id="job-123", status=ProcessingJobStatus.QUEUED)

    monkeypatch.setattr(
        ProcessingJobLifecycle,
        "enqueue",
        classmethod(fake_enqueue),
    )

    file_content = b"video-binary-data"

    response = client.post(
        "/assets/upload",
        data={
            "project_id": project.id,
            "asset_type": "source",
        },
        files={
            "file": ("clip.mp4", io.BytesIO(file_content), "video/mp4"),
        },
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["project_id"] == project.id
    assert payload["filename"] == "clip.mp4"
    assert payload["job_id"] == "job-123"
    assert payload["job_status"] == ProcessingJobStatus.QUEUED.value
    assert created_jobs
    job_payload = created_jobs[0]["payload"]
    assert job_payload["asset_id"] == payload["asset_id"]

    repository = MediaAssetRepository(db_session)
    stored_assets = repository.list()
    assert len(stored_assets) == 1
    stored_asset = stored_assets[0]
    assert stored_asset.filename == "clip.mp4"
    assert stored_asset.project_id == project.id
    assert stored_asset.size_bytes == len(file_content)


def test_upload_asset_handles_job_enqueue_failure(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = Project(id="proj-failure", name="Failure Project", status=ProjectStatus.ACTIVE)
    db_session.add(project)
    db_session.commit()

    def failing_enqueue(
        cls,
        *,
        job_type,
        payload,
        clip_version_id=None,
        priority=0,
        queue_name=None,
    ):
        raise RuntimeError("queue offline")

    monkeypatch.setattr(
        ProcessingJobLifecycle,
        "enqueue",
        classmethod(failing_enqueue),
    )

    response = client.post(
        "/assets/upload",
        data={
            "project_id": project.id,
            "asset_type": "source",
        },
        files={
            "file": ("clip.mp4", io.BytesIO(b"content"), "video/mp4"),
        },
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["warning"].startswith("Asset uploaded")
    assert payload["job_id"] is None
    assert payload["job_status"] is None


def test_list_assets_with_filters(
    client: TestClient,
    db_session: Session,
    settings: TestingSettings,
) -> None:
    project_a = Project(id="proj-a", name="Project A", status=ProjectStatus.ACTIVE)
    project_b = Project(id="proj-b", name="Project B", status=ProjectStatus.ACTIVE)
    db_session.add_all([project_a, project_b])
    db_session.commit()

    repository = MediaAssetRepository(db_session)
    storage = StorageService(settings, repository)

    for idx in range(3):
        storage.ingest_media_asset(
            project_id=project_a.id,
            asset_type=MediaAssetType.SOURCE,
            fileobj=io.BytesIO(b"a" * (idx + 1)),
            filename=f"a{idx}.mp4",
        )
    storage.ingest_media_asset(
        project_id=project_b.id,
        asset_type=MediaAssetType.GENERATED,
        fileobj=io.BytesIO(b"b-data"),
        filename="b.mp4",
    )

    response = client.get(f"/assets/?project_id={project_a.id}&limit=2")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert len(payload["items"]) == 2
    for item in payload["items"]:
        assert item["project_id"] == project_a.id


def test_get_asset_not_found_returns_404(client: TestClient) -> None:
    response = client.get("/assets/nonexistent")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["message"].lower()
