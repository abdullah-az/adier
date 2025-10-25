from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from fastapi import UploadFile

from app.repositories.video_repository import VideoAssetRepository
from app.services.storage_service import StorageService
from app.utils.storage import DEFAULT_CATEGORIES, StorageManager


@pytest.fixture()
def storage_components(tmp_path: Path):
    storage_manager = StorageManager(storage_root=tmp_path)
    video_repository = VideoAssetRepository(storage_root=tmp_path)
    service = StorageService(storage_manager=storage_manager, video_repository=video_repository)
    return storage_manager, video_repository, service


def _build_upload(filename: str, content: bytes) -> UploadFile:
    file_stream = BytesIO(content)
    upload = UploadFile(filename=filename, file=file_stream, content_type="video/mp4")
    return upload


@pytest.mark.asyncio
async def test_upload_and_cleanup_removes_project_storage(storage_components):
    storage_manager, repository, service = storage_components

    upload = _build_upload("lesson.mp4", b"fake video bytes" * 1024)
    asset = await service.upload_video("demo-project", upload, generate_thumbnail=False)

    # Ensure file persisted
    stored_video = storage_manager.storage_root / asset.relative_path
    assert stored_video.exists()

    # Ensure metadata stored
    stored_assets = await repository.list_by_project("demo-project")
    assert stored_assets and stored_assets[0].id == asset.id

    # Perform cleanup
    await service.delete_project_storage("demo-project")

    # All project directories removed
    for category in DEFAULT_CATEGORIES:
        category_dir = storage_manager.storage_root / category
        assert not any(child.name == "demo-project" for child in category_dir.iterdir())

    # Metadata cleared
    assert await repository.list_by_project("demo-project") == []


@pytest.mark.asyncio
async def test_invalid_extension_rejected(storage_components):
    _, repository, service = storage_components

    bad_upload = UploadFile(filename="notes.txt", file=BytesIO(b"invalid"), content_type="text/plain")

    with pytest.raises(ValueError):
        await service.upload_video("demo", bad_upload, generate_thumbnail=False)

    assert await repository.all_assets() == []
