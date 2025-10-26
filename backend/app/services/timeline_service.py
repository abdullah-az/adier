from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Sequence

from loguru import logger

from app.models.timeline import (
    MusicTrack,
    TimelineMusicSettings,
    TimelineSettings,
    SubtitleSegment,
)
from app.repositories.timeline_repository import TimelineSettingsRepository
from app.utils.storage import StorageManager

_AUDIO_EXTENSIONS = {".mp3", ".wav", ".aac", ".m4a", ".flac", ".ogg"}


class TimelineSettingsService:
    """Coordinates subtitle and background music settings for timelines."""

    def __init__(
        self,
        repository: TimelineSettingsRepository,
        storage_manager: StorageManager,
    ) -> None:
        self.repository = repository
        self.storage_manager = storage_manager

    async def _ensure_settings(self, project_id: str) -> TimelineSettings:
        settings = await self.repository.get(project_id)
        if settings is None:
            settings = TimelineSettings(project_id=project_id)
            await self.repository.upsert(settings)
        return settings

    async def get_settings(self, project_id: str) -> TimelineSettings:
        settings = await self._ensure_settings(project_id)
        settings.subtitles = settings.ordered_subtitles()
        return settings

    async def list_subtitles(self, project_id: str) -> List[SubtitleSegment]:
        settings = await self._ensure_settings(project_id)
        ordered = settings.ordered_subtitles()
        settings.subtitles = ordered
        return ordered

    async def update_subtitles(
        self,
        project_id: str,
        segments: Sequence[SubtitleSegment | dict],
    ) -> TimelineSettings:
        validated: list[SubtitleSegment] = []
        for raw in segments:
            if isinstance(raw, SubtitleSegment):
                segment = raw
            else:
                segment = SubtitleSegment.model_validate(raw)
            segment = segment.model_copy(update={
                "start": max(0.0, float(segment.start)),
                "end": max(float(segment.end), max(0.01, float(segment.start) + 0.01)),
            })
            validated.append(segment)

        validated.sort(key=lambda seg: seg.start)

        settings = await self._ensure_settings(project_id)
        settings.subtitles = validated
        settings.updated_at = datetime.utcnow()
        updated = await self.repository.upsert(settings)
        logger.debug(
            "Updated subtitle timeline",
            project_id=project_id,
            segment_count=len(validated),
        )
        return updated

    async def list_music_tracks(self, project_id: str) -> List[MusicTrack]:
        self.storage_manager.ensure_project_directories(project_id)
        music_dir = self.storage_manager.project_category_path(project_id, "music")
        tracks: list[MusicTrack] = []

        if not music_dir.exists():
            return tracks

        for path in music_dir.iterdir():
            if not path.is_file():
                continue
            if path.suffix.lower() not in _AUDIO_EXTENSIONS:
                continue
            relative_path = str(path.relative_to(self.storage_manager.storage_root))
            display_name = self._format_display_name(path)
            track = MusicTrack(
                track_id=path.name,
                filename=path.name,
                display_name=display_name,
                relative_path=relative_path,
                size_bytes=path.stat().st_size,
            )
            tracks.append(track)

        tracks.sort(key=lambda track: track.display_name.lower())
        return tracks

    async def get_music_settings(self, project_id: str) -> TimelineMusicSettings:
        settings = await self._ensure_settings(project_id)
        return settings.music

    async def update_music_settings(
        self,
        project_id: str,
        music_settings: TimelineMusicSettings | dict,
    ) -> TimelineSettings:
        if isinstance(music_settings, TimelineMusicSettings):
            music = music_settings
        else:
            music = TimelineMusicSettings.model_validate(music_settings)

        if music.is_enabled and music.track_id:
            await self._assert_track_exists(project_id, music.track_id)

        settings = await self._ensure_settings(project_id)
        settings.music = music
        settings.updated_at = datetime.utcnow()
        updated = await self.repository.upsert(settings)
        logger.debug(
            "Updated music settings",
            project_id=project_id,
            track_id=music.track_id,
            enabled=music.is_enabled,
        )
        return updated

    async def _assert_track_exists(self, project_id: str, track_id: str) -> None:
        music_dir = self.storage_manager.project_category_path(project_id, "music")
        path = music_dir / track_id
        if not path.exists() or not path.is_file():
            raise ValueError(f"Track '{track_id}' not found in project music library")

    def _format_display_name(self, path: Path) -> str:
        stem = path.stem.replace("_", " ").replace("-", " ")
        return " ".join(part.capitalize() for part in stem.split()) or path.stem

    async def delete_settings(self, project_id: str) -> None:
        await self.repository.delete(project_id)
        logger.debug("Cleared timeline settings", project_id=project_id)
