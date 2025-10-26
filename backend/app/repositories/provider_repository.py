"""Persistence layer for AI provider configuration and usage metadata."""

from __future__ import annotations

import asyncio
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Optional

from loguru import logger


_DEFAULT_STATE: dict[str, Any] = {
    "priority": [],
    "project_overrides": {},
    "usage": {},
}


class ProviderConfigRepository:
    """Store provider configuration in the metadata directory."""

    def __init__(self, storage_root: str | Path) -> None:
        self.storage_root = Path(storage_root).resolve()
        self.metadata_dir = self.storage_root / "metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.metadata_dir / "ai_providers.json"
        self._lock: Optional[asyncio.Lock] = None

    async def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def load_state(self) -> dict[str, Any]:
        if not self.metadata_file.exists():
            return deepcopy(_DEFAULT_STATE)

        def _read() -> dict[str, Any]:
            with self.metadata_file.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
            if not isinstance(payload, dict):
                return deepcopy(_DEFAULT_STATE)
            return payload

        state = await asyncio.to_thread(_read)
        for key, default_value in _DEFAULT_STATE.items():
            state.setdefault(key, deepcopy(default_value))
        return state

    async def save_state(self, state: dict[str, Any]) -> None:
        lock = await self._get_lock()
        async with lock:
            await asyncio.to_thread(self._write_state, state)

    def _write_state(self, state: dict[str, Any]) -> None:
        tmp_file = self.metadata_dir / "ai_providers.tmp"
        with tmp_file.open("w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2, sort_keys=True)
        tmp_file.replace(self.metadata_file)
        logger.debug("Persisted AI provider metadata", path=str(self.metadata_file))

    async def reset(self) -> None:
        lock = await self._get_lock()
        async with lock:
            if self.metadata_file.exists():
                self.metadata_file.unlink()
        logger.debug("Reset AI provider configuration state")

    @staticmethod
    def default_state() -> dict[str, Any]:
        return deepcopy(_DEFAULT_STATE)
