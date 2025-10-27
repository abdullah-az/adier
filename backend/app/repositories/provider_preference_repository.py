from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Dict, Optional, Union


class ProviderPreferenceRepository:
    """Persist per-project provider preferences in JSON storage."""

    def __init__(self, storage_root: Union[str, Path]) -> None:
        self.storage_root = Path(storage_root)
        self.metadata_dir = self.storage_root / "metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.metadata_dir / "provider_preferences.json"
        self._lock: Optional[asyncio.Lock] = None

    async def _load(self) -> Dict[str, Dict[str, str]]:
        if not self.metadata_file.exists():
            return {}

        def _read() -> Dict[str, Dict[str, str]]:
            with self.metadata_file.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
            return {project_id: dict(mapping) for project_id, mapping in payload.items()}

        return await asyncio.to_thread(_read)

    async def _persist(self, payload: Dict[str, Dict[str, str]]) -> None:
        def _write() -> None:
            tmp = self.metadata_dir / "provider_preferences.tmp"
            with tmp.open("w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2, sort_keys=True)
            tmp.replace(self.metadata_file)

        await asyncio.to_thread(_write)

    async def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def get_preferences(self, project_id: str) -> Dict[str, str]:
        data = await self._load()
        return dict(data.get(project_id, {}))

    async def set_preferences(self, project_id: str, preferences: Dict[str, str]) -> Dict[str, str]:
        lock = await self._get_lock()
        async with lock:
            data = await self._load()
            if preferences:
                data[project_id] = dict(preferences)
            else:
                data.pop(project_id, None)
            await self._persist(data)
            return dict(data.get(project_id, {}))

    async def delete_project(self, project_id: str) -> None:
        await self.set_preferences(project_id, {})

    async def list_all(self) -> Dict[str, Dict[str, str]]:
        return await self._load()
