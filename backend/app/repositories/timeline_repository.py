from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import List, Optional, Union

from app.models.timeline import Timeline


class TimelineRepository:
    """Repository persisted as JSON for storing timeline blueprints."""

    def __init__(self, storage_root: Union[str, Path]) -> None:
        self.storage_root = Path(storage_root).resolve()
        self.metadata_dir = self.storage_root / "metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.metadata_dir / "timelines.json"
        self._lock: Optional[asyncio.Lock] = None

    async def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def _load(self) -> List[Timeline]:
        if not self.metadata_file.exists():
            return []

        def _read() -> List[Timeline]:
            with self.metadata_file.open("r", encoding="utf-8") as buffer:
                payload = json.load(buffer)
            return [Timeline(**record) for record in payload]

        return await asyncio.to_thread(_read)

    async def _persist(self, timelines: List[Timeline]) -> None:
        def _write() -> None:
            tmp_file = self.metadata_dir / "timelines.tmp"
            with tmp_file.open("w", encoding="utf-8") as buffer:
                json.dump([timeline.model_dump() for timeline in timelines], buffer, indent=2)
            tmp_file.replace(self.metadata_file)

        await asyncio.to_thread(_write)

    async def add(self, timeline: Timeline) -> Timeline:
        lock = await self._get_lock()
        async with lock:
            timelines = await self._load()
            timelines = [existing for existing in timelines if existing.id != timeline.id]
            timelines.append(timeline)
            await self._persist(timelines)
            return timeline

    async def update(self, timeline: Timeline) -> Timeline:
        return await self.add(timeline)

    async def get(self, timeline_id: str) -> Optional[Timeline]:
        timelines = await self._load()
        return next((timeline for timeline in timelines if timeline.id == timeline_id), None)

    async def list_by_project(self, project_id: str) -> List[Timeline]:
        timelines = await self._load()
        return [timeline for timeline in timelines if timeline.project_id == project_id]

    async def delete(self, timeline_id: str) -> None:
        lock = await self._get_lock()
        async with lock:
            timelines = await self._load()
            timelines = [timeline for timeline in timelines if timeline.id != timeline_id]
            await self._persist(timelines)

    async def delete_for_project(self, project_id: str) -> None:
        lock = await self._get_lock()
        async with lock:
            timelines = await self._load()
            timelines = [timeline for timeline in timelines if timeline.project_id != project_id]
            await self._persist(timelines)

    async def all_timelines(self) -> List[Timeline]:
        return await self._load()
