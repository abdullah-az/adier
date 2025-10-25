from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import List, Optional, Union

from loguru import logger

from app.models.transcription import Transcript


class TranscriptRepository:
    """Persist transcripts and subtitle segments to JSON storage."""

    def __init__(self, storage_root: Union[str, Path]) -> None:
        self.storage_root = Path(storage_root).resolve()
        self.metadata_dir = self.storage_root / "metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.metadata_dir / "transcripts.json"
        self._lock: Optional[asyncio.Lock] = None

    async def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def _load_transcripts(self) -> List[Transcript]:
        if not self.metadata_file.exists():
            return []

        def _read() -> List[Transcript]:
            with self.metadata_file.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            return [Transcript.model_validate(entry) for entry in payload]

        return await asyncio.to_thread(_read)

    async def _persist(self, transcripts: List[Transcript]) -> None:
        def _write() -> None:
            tmp = self.metadata_dir / "transcripts.tmp"
            with tmp.open("w", encoding="utf-8") as handle:
                json.dump([item.model_dump(mode="json") for item in transcripts], handle, indent=2)
            tmp.replace(self.metadata_file)

        await asyncio.to_thread(_write)

    async def save(self, transcript: Transcript, *, replace_existing: bool = True) -> Transcript:
        """Persist a transcript, optionally replacing any prior entry for the asset."""
        lock = await self._get_lock()
        async with lock:
            transcripts = await self._load_transcripts()
            if replace_existing:
                transcripts = [item for item in transcripts if item.asset_id != transcript.asset_id]
            transcripts = [item for item in transcripts if item.id != transcript.id]
            transcripts.append(transcript)
            await self._persist(transcripts)
            logger.debug(
                "Saved transcript",
                transcript_id=transcript.id,
                asset_id=transcript.asset_id,
                project_id=transcript.project_id,
            )
            return transcript

    async def get_by_asset(self, asset_id: str) -> Optional[Transcript]:
        transcripts = await self._load_transcripts()
        return next((item for item in transcripts if item.asset_id == asset_id), None)

    async def list_by_project(self, project_id: str) -> List[Transcript]:
        transcripts = await self._load_transcripts()
        filtered = [item for item in transcripts if item.project_id == project_id]
        filtered.sort(key=lambda entry: entry.created_at, reverse=True)
        return filtered

    async def delete_for_asset(self, asset_id: str) -> None:
        lock = await self._get_lock()
        async with lock:
            transcripts = await self._load_transcripts()
            transcripts = [item for item in transcripts if item.asset_id != asset_id]
            await self._persist(transcripts)
            logger.debug("Deleted transcript entries", asset_id=asset_id)
