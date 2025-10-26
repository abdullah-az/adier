from __future__ import annotations

from pathlib import Path

import pytest

from app.utils.storage import DEFAULT_CATEGORIES, StorageManager


@pytest.fixture
def storage_manager(temp_storage_dir: Path) -> StorageManager:
    return StorageManager(storage_root=temp_storage_dir)


def test_validate_video_file_accepts_supported_extensions(storage_manager: StorageManager):
    for name in ["demo.mp4", "clip.MOV", "sample.AVI"]:
        storage_manager.validate_video_file(name)


def test_validate_video_file_rejects_unsupported_extension(storage_manager: StorageManager):
    with pytest.raises(ValueError):
        storage_manager.validate_video_file("notes.txt")


def test_build_thumbnail_path_uses_sanitized_stem(storage_manager: StorageManager):
    path = storage_manager.build_thumbnail_path("proj 1", "My Video.mov")
    assert path.name.endswith(".jpg")
    assert "my-video" in path.stem


def test_storage_usage_counts_files(storage_manager: StorageManager, sample_video_bytes: bytes):
    project_id = "project-alpha"
    storage_manager.ensure_project_directories(project_id)

    uploads_dir = storage_manager.project_category_path(project_id, "uploads")
    processed_dir = storage_manager.project_category_path(project_id, "processed")

    (uploads_dir / "clip.mp4").write_bytes(sample_video_bytes)
    (processed_dir / "clip.mp4").write_bytes(sample_video_bytes)

    usage = storage_manager.storage_usage()
    assert usage["categories"]["uploads"]["file_count"] == 1
    assert usage["categories"]["processed"]["file_count"] == 1


def test_project_storage_usage_isolated_by_project(storage_manager: StorageManager, sample_video_bytes: bytes):
    project_id = "proj-123"
    other_project = "proj-999"

    storage_manager.ensure_project_directories(project_id)
    storage_manager.ensure_project_directories(other_project)

    project_uploads = storage_manager.project_category_path(project_id, "uploads")
    other_uploads = storage_manager.project_category_path(other_project, "uploads")

    (project_uploads / "video.mp4").write_bytes(sample_video_bytes)
    (other_uploads / "skip.mp4").write_bytes(sample_video_bytes)

    stats = storage_manager.project_storage_usage(project_id)
    other_stats = storage_manager.project_storage_usage(other_project)

    assert stats["categories"]["uploads"]["file_count"] == 1
    assert other_stats["categories"]["uploads"]["file_count"] == 1


def test_cleanup_project_removes_all_category_directories(storage_manager: StorageManager):
    project_id = "proj-cleanup"
    storage_manager.ensure_project_directories(project_id)
    storage_manager.cleanup_project(project_id)

    for category in DEFAULT_CATEGORIES:
        category_dir = storage_manager.project_category_path(project_id, category)
        assert not category_dir.exists()
