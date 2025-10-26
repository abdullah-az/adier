from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union

from loguru import logger

from app.models.timeline import TimelineSettings


class TimelineSettingsRepository:
    """JSON-backed persistence for per-project timeline settings."""

    def __init__(self, storage_root: Union[str, Path]) -> None:
        self.storage_root = Path(storage_root).resolve()
        self.metadata_dir = self.storage_root / "metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.metadata_dir / "timeline_settings.json"
        self._lock: Optional[asyncio.Lock] = None

    async def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def _load_all(self) -> Dict[str, TimelineSettings]:
        if not self.metadata_file.exists():
            return {}

        def _read() -> Dict[str, TimelineSettings]:
            with self.metadata_file.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)

            settings_map: Dict[str, TimelineSettings] = {}
            if isinstance(payload, dict) and all(isinstance(v, dict) for v in payload.values()):
                for project_key, item in payload.items():
                    entry = item if "project_id" in item else {**item, "project_id": project_key}
                    settings = TimelineSettings.model_validate(entry)
                    settings_map[settings.project_id] = settings
                return settings_map

            # legacy list-based layout fallback
            if isinstance(payload, list):
                for item in payload:
                    if not isinstance(item, dict):
                        continue
                    settings = TimelineSettings.model_validate(item)
                    settings_map[settings.project_id] = settings
            return settings_map

        return await asyncio.to_thread(_read)

    async def _persist(self, settings: Dict[str, TimelineSettings]) -> None:
        def _write() -> None:
            serialised = {
                project_id: timeline.model_dump(mode="json")
                for project_id, timeline in settings.items()
            }
            temp_file = self.metadata_dir / "timeline_settings.tmp"
            with temp_file.open("w", encoding="utf-8") as fh:
                json.dump(serialised, fh, indent=2)
            temp_file.replace(self.metadata_file)

        await asyncio.to_thread(_write)

    async def get(self, project_id: str) -> Optional[TimelineSettings]:
        settings = await self._load_all()
        return settings.get(project_id)

    async def upsert(self, timeline: TimelineSettings) -> TimelineSettings:
        lock = await self._get_lock()
        async with lock:
            settings = await self._load_all()
            timeline.updated_at = datetime.utcnow()
            settings[timeline.project_id] = timeline
            await self._persist(settings)
            logger.debug("Persisted timeline settings", project_id=timeline.project_id)
            return timeline

    async def delete(self, project_id: str) -> None:
        lock = await self._get_lock()
        async with lock:
            settings = await self._load_all()
            if project_id in settings:
                settings.pop(project_id)
                await self._persist(settings)
                logger.debug("Deleted timeline settings", project_id=project_id)

    async def all_settings(self) -> Dict[str, TimelineSettings]:
        return await self._load_all()
