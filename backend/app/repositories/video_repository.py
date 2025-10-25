from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import List, Optional, Union

from loguru import logger

from app.models.video_asset import VideoAsset


class VideoAssetRepository:
    """Repository persisted to JSON for storing video asset metadata."""

    def __init__(self, storage_root: Union[str, Path]) -> None:
        self.storage_root = Path(storage_root).resolve()
        self.metadata_dir = self.storage_root / "metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.metadata_dir / "video_assets.json"
        self._lock: Optional[asyncio.Lock] = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _load_assets(self) -> List[VideoAsset]:
        if not self.metadata_file.exists():
            return []

        def _read() -> List[VideoAsset]:
            with self.metadata_file.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
            return [VideoAsset(**item) for item in payload]

        return await asyncio.to_thread(_read)

    async def _persist(self, assets: List[VideoAsset]) -> None:
        def _write() -> None:
            tmp_file = self.metadata_dir / "video_assets.tmp"
            with tmp_file.open("w", encoding="utf-8") as fh:
                json.dump([asset.model_dump() for asset in assets], fh, indent=2)
            tmp_file.replace(self.metadata_file)

        await asyncio.to_thread(_write)

    async def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------
    async def add(self, asset: VideoAsset) -> VideoAsset:
        lock = await self._get_lock()
        async with lock:
            assets = await self._load_assets()
            assets.append(asset)
            await self._persist(assets)
            logger.debug("Registered video asset", asset_id=asset.id, project_id=asset.project_id)
            return asset

    async def update(self, asset: VideoAsset) -> VideoAsset:
        lock = await self._get_lock()
        async with lock:
            assets = await self._load_assets()
            assets = [existing for existing in assets if existing.id != asset.id]
            assets.append(asset)
            await self._persist(assets)
            logger.debug("Updated video asset", asset_id=asset.id)
            return asset

    async def get(self, asset_id: str) -> Optional[VideoAsset]:
        assets = await self._load_assets()
        return next((asset for asset in assets if asset.id == asset_id), None)

    async def list_by_project(self, project_id: str) -> List[VideoAsset]:
        assets = await self._load_assets()
        return [asset for asset in assets if asset.project_id == project_id]

    async def delete(self, asset_id: str) -> None:
        lock = await self._get_lock()
        async with lock:
            assets = await self._load_assets()
            assets = [asset for asset in assets if asset.id != asset_id]
            await self._persist(assets)
            logger.debug("Deleted video asset metadata", asset_id=asset_id)

    async def delete_for_project(self, project_id: str) -> None:
        lock = await self._get_lock()
        async with lock:
            assets = await self._load_assets()
            assets = [asset for asset in assets if asset.project_id != project_id]
            await self._persist(assets)
            logger.debug("Removed video assets for project", project_id=project_id)

    async def all_assets(self) -> List[VideoAsset]:
        return await self._load_assets()
