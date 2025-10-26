from __future__ import annotations

from pathlib import Path

import pytest

from app.repositories.timeline_repository import TimelineSettingsRepository
from app.services.timeline_service import TimelineSettingsService
from app.utils.storage import StorageManager


@pytest.fixture()
def timeline_components(tmp_path: Path):
    storage_manager = StorageManager(storage_root=tmp_path)
    repository = TimelineSettingsRepository(storage_root=tmp_path)
    service = TimelineSettingsService(repository=repository, storage_manager=storage_manager)
    return storage_manager, repository, service


@pytest.mark.asyncio
async def test_update_and_fetch_subtitles(timeline_components):
    _, _, service = timeline_components
    project_id = "demo"

    await service.update_subtitles(
        project_id,
        [
            {
                "id": "seg-1",
                "start": 0.0,
                "end": 2.5,
                "text": "Hello world",
                "language": "en",
                "is_visible": True,
            },
            {
                "id": "seg-2",
                "start": 2.5,
                "end": 5.0,
                "text": "مرحبا",
                "language": "ar",
                "is_visible": True,
            },
        ],
    )

    settings = await service.get_settings(project_id)
    assert len(settings.subtitles) == 2
    assert settings.subtitles[0].text == "Hello world"
    assert settings.subtitles[1].language == "ar"


@pytest.mark.asyncio
async def test_music_tracks_listing(timeline_components):
    storage_manager, _, service = timeline_components
    project_id = "demo"
    music_dir = storage_manager.project_category_path(project_id, "music")
    music_dir.mkdir(parents=True, exist_ok=True)
    track_path = music_dir / "calm-track.mp3"
    track_path.write_bytes(b"audio")

    tracks = await service.list_music_tracks(project_id)
    assert tracks
    assert tracks[0].track_id == "calm-track.mp3"
    assert tracks[0].relative_path.endswith("calm-track.mp3")


@pytest.mark.asyncio
async def test_update_music_requires_existing_track(timeline_components):
    storage_manager, _, service = timeline_components
    project_id = "demo"
    music_dir = storage_manager.project_category_path(project_id, "music")
    music_dir.mkdir(parents=True, exist_ok=True)
    (music_dir / "bed.mp3").write_bytes(b"audio")

    await service.update_music_settings(
        project_id,
        {
            "track_id": "bed.mp3",
            "volume": 0.5,
            "fade_in": 1.0,
            "fade_out": 1.0,
            "offset": 0.0,
            "placement": "full_timeline",
            "loop": True,
            "is_enabled": True,
        },
    )

    with pytest.raises(ValueError):
        await service.update_music_settings(
            project_id,
            {
                "track_id": "missing.mp3",
                "volume": 0.5,
                "fade_in": 1.0,
                "fade_out": 1.0,
                "offset": 0.0,
                "placement": "full_timeline",
                "loop": True,
                "is_enabled": True,
            },
        )
