from __future__ import annotations

import hashlib
import io
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import TestingSettings
from backend.app.models.base import Base
from backend.app.models.enums import MediaAssetType
from backend.app.repositories.media_asset import MediaAssetRepository
from backend.app.services.storage_service import (
    AssetFileMissingError,
    AssetNotFoundError,
    ChecksumMismatchError,
    StorageQuotaExceeded,
    StorageService,
)
from backend.app.utils.pathing import asset_relative_path, ensure_within_root, normalise_component


@pytest.fixture()
def db_session(tmp_path: Path) -> Session:
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    with TestingSession() as session:
        yield session
    engine.dispose()


def _make_service(
    tmp_path: Path, session: Session, *, storage_max_bytes: int | None = None
) -> tuple[StorageService, TestingSettings]:
    settings = TestingSettings(
        storage_root=str(tmp_path / "storage"),
        storage_temp=str(tmp_path / "temp"),
        storage_max_bytes=storage_max_bytes,
    )
    repository = MediaAssetRepository(session)
    return StorageService(settings, repository), settings


def test_asset_relative_path_is_deterministic() -> None:
    relative_path = asset_relative_path(
        "Project 123",
        MediaAssetType.SOURCE,
        "Asset Variant",
        "My Clip.MP4",
    )
    assert relative_path == Path("project-123/source/asset-variant/my-clip.mp4")
    assert normalise_component("Project 123") == "project-123"


def test_ensure_within_root_guard(tmp_path: Path) -> None:
    root = tmp_path / "store"
    root.mkdir()
    with pytest.raises(ValueError):
        ensure_within_root(root, "../escape.mp4")


def test_ingest_and_delete_media_asset(tmp_path: Path, db_session: Session) -> None:
    service, _settings = _make_service(tmp_path, db_session)
    file_bytes = b"video-contents"
    checksum = hashlib.sha256(file_bytes).hexdigest()
    asset = service.ingest_media_asset(
        project_id="proj-123",
        asset_type=MediaAssetType.SOURCE,
        fileobj=io.BytesIO(file_bytes),
        filename="Sample.mp4",
        mime_type="video/mp4",
        duration_seconds=12.5,
        expected_checksum=checksum,
    )

    assert asset.file_path.endswith("sample.mp4")

    stored_path = service.resolve_asset_path(asset.id)
    assert stored_path.exists()
    assert stored_path.read_bytes() == file_bytes
    assert asset.size_bytes == len(file_bytes)
    assert asset.checksum == checksum

    signed_path = service.generate_signed_path(asset.id, expires_in=60)
    assert signed_path.path == str(stored_path)
    assert signed_path.size_bytes == len(file_bytes)
    assert signed_path.mime_type == "video/mp4"
    assert signed_path.expires_at > datetime.now(timezone.utc)

    usage = service.report_space_usage()
    assert usage.used_bytes == len(file_bytes)
    assert usage.max_bytes is None

    service.delete_media_asset(asset.id)

    with pytest.raises(AssetNotFoundError):
        service.resolve_asset_path(asset.id)

    assert not stored_path.exists()


def test_delete_reports_missing_file(tmp_path: Path, db_session: Session) -> None:
    service, _settings = _make_service(tmp_path, db_session)
    asset = service.ingest_media_asset(
        project_id="proj-123",
        asset_type=MediaAssetType.SOURCE,
        fileobj=io.BytesIO(b"content"),
        filename="missing.mp4",
    )

    stored_path = service.resolve_asset_path(asset.id)
    stored_path.unlink()

    with pytest.raises(AssetFileMissingError):
        service.delete_media_asset(asset.id)

    # record is removed even when file is already gone
    with pytest.raises(AssetNotFoundError):
        service.resolve_asset_path(asset.id)


def test_ingest_with_incorrect_checksum(tmp_path: Path, db_session: Session) -> None:
    service, _settings = _make_service(tmp_path, db_session)

    with pytest.raises(ChecksumMismatchError):
        service.ingest_media_asset(
            project_id="proj-123",
            asset_type=MediaAssetType.SOURCE,
            fileobj=io.BytesIO(b"abcdef"),
            filename="clip.mp4",
            expected_checksum="deadbeef",
        )


def test_quota_enforced(tmp_path: Path, db_session: Session) -> None:
    service, settings = _make_service(tmp_path, db_session, storage_max_bytes=4)

    with pytest.raises(StorageQuotaExceeded):
        service.ingest_media_asset(
            project_id="proj-123",
            asset_type=MediaAssetType.SOURCE,
            fileobj=io.BytesIO(b"too-big"),
            filename="clip.mp4",
        )

    assert not any(settings.storage_root.rglob("*"))


def test_repository_update_metadata(tmp_path: Path, db_session: Session) -> None:
    service, _settings = _make_service(tmp_path, db_session)
    asset = service.ingest_media_asset(
        project_id="proj-123",
        asset_type=MediaAssetType.SOURCE,
        fileobj=io.BytesIO(b"data"),
        filename="clip.mp4",
    )

    repository = MediaAssetRepository(db_session)
    updated = repository.update_metadata(asset, size_bytes=123, duration_seconds=4.5)

    assert updated.size_bytes == 123
    assert pytest.approx(updated.duration_seconds or 0, rel=1e-6) == 4.5
