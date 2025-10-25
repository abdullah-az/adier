from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import List, Optional, Union

from loguru import logger

from app.models.scene import SceneAnalysis


class SceneAnalysisRepository:
    """Repository for persisting AI scene detection analyses."""

    def __init__(self, storage_root: Union[str, Path]) -> None:
        self.storage_root = Path(storage_root).resolve()
        self.metadata_dir = self.storage_root / "metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.metadata_dir / "scene_detections.json"
        self._lock: Optional[asyncio.Lock] = None

    async def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def _load(self) -> List[SceneAnalysis]:
        if not self.metadata_file.exists():
            return []

        def _read() -> List[SceneAnalysis]:
            with self.metadata_file.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            return [SceneAnalysis.model_validate(entry) for entry in payload]

        return await asyncio.to_thread(_read)

    async def _persist(self, analyses: List[SceneAnalysis]) -> None:
        def _write() -> None:
            tmp = self.metadata_dir / "scene_detections.tmp"
            with tmp.open("w", encoding="utf-8") as handle:
                json.dump([item.model_dump(mode="json") for item in analyses], handle, indent=2)
            tmp.replace(self.metadata_file)

        await asyncio.to_thread(_write)

    async def save(self, analysis: SceneAnalysis, *, replace_existing: bool = True) -> SceneAnalysis:
        """Persist a scene analysis entry."""
        lock = await self._get_lock()
        async with lock:
            analyses = await self._load()
            if replace_existing:
                analyses = [item for item in analyses if item.asset_id != analysis.asset_id]
            analyses = [item for item in analyses if item.id != analysis.id]
            analyses.append(analysis)
            await self._persist(analyses)
            logger.debug(
                "Saved scene analysis",
                analysis_id=analysis.id,
                asset_id=analysis.asset_id,
                project_id=analysis.project_id,
            )
            return analysis

    async def list_by_project(self, project_id: str) -> List[SceneAnalysis]:
        analyses = await self._load()
        filtered = [item for item in analyses if item.project_id == project_id]
        filtered.sort(key=lambda entry: entry.created_at, reverse=True)
        return filtered

    async def list_by_asset(self, asset_id: str) -> List[SceneAnalysis]:
        analyses = await self._load()
        filtered = [item for item in analyses if item.asset_id == asset_id]
        filtered.sort(key=lambda entry: entry.created_at, reverse=True)
        return filtered

    async def get_latest_for_asset(self, asset_id: str) -> Optional[SceneAnalysis]:
        analyses = await self.list_by_asset(asset_id)
        return analyses[0] if analyses else None

    async def delete_for_asset(self, asset_id: str) -> None:
        lock = await self._get_lock()
        async with lock:
            analyses = await self._load()
            analyses = [item for item in analyses if item.asset_id != asset_id]
            await self._persist(analyses)
            logger.debug("Deleted scene analyses", asset_id=asset_id)
