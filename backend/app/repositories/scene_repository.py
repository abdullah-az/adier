from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import List, Optional

from loguru import logger

from app.models.scene_detection import SceneDetectionRun


class SceneDetectionRepository:
    """Persist scene detection analysis runs to JSON files, grouped per asset."""

    def __init__(self, storage_root: str | Path) -> None:
        self.storage_root = Path(storage_root).resolve()
        self.base_dir = self.storage_root / "metadata" / "scenes"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._locks: dict[str, asyncio.Lock] = {}
        self._lock_guard = asyncio.Lock()

    async def _get_lock(self, asset_id: str) -> asyncio.Lock:
        async with self._lock_guard:
            if asset_id not in self._locks:
                self._locks[asset_id] = asyncio.Lock()
            return self._locks[asset_id]

    def _asset_dir(self, asset_id: str) -> Path:
        safe_id = asset_id.replace("/", "_")
        return self.base_dir / safe_id

    async def save_run(self, run: SceneDetectionRun) -> SceneDetectionRun:
        lock = await self._get_lock(run.asset_id)
        async with lock:
            asset_dir = self._asset_dir(run.asset_id)
            asset_dir.mkdir(parents=True, exist_ok=True)
            path = asset_dir / f"{run.id}.json"

            def _write() -> None:
                tmp_path = path.with_suffix(".tmp")
                with tmp_path.open("w", encoding="utf-8") as handle:
                    json.dump(run.model_dump(mode="json"), handle, indent=2)
                tmp_path.replace(path)

            await asyncio.to_thread(_write)
            logger.info(
                "Persisted scene detection run",
                asset_id=run.asset_id,
                project_id=run.project_id,
                scenes=run.scene_count,
            )
            return run

    async def list_runs(self, asset_id: str) -> List[SceneDetectionRun]:
        asset_dir = self._asset_dir(asset_id)
        if not asset_dir.exists():
            return []

        def _read_all() -> List[SceneDetectionRun]:
            runs: List[SceneDetectionRun] = []
            for file_path in sorted(asset_dir.glob("*.json")):
                with file_path.open("r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                try:
                    run = SceneDetectionRun.model_validate(payload)
                except Exception as exc:  # pragma: no cover - defensive against corrupt files
                    logger.warning(
                        "Skipping invalid scene detection file",
                        path=str(file_path),
                        error=str(exc),
                    )
                    continue
                runs.append(run)
            return runs

        return await asyncio.to_thread(_read_all)

    async def get_latest(self, asset_id: str) -> Optional[SceneDetectionRun]:
        runs = await self.list_runs(asset_id)
        if not runs:
            return None
        runs.sort(key=lambda item: item.generated_at, reverse=True)
        return runs[0]

    async def delete_runs(self, asset_id: str) -> None:
        lock = await self._get_lock(asset_id)
        async with lock:
            asset_dir = self._asset_dir(asset_id)
            if not asset_dir.exists():
                return
            for path in asset_dir.glob("*.json"):
                path.unlink(missing_ok=True)
            logger.debug("Deleted scene detection runs", asset_id=asset_id)


__all__ = ["SceneDetectionRepository"]
