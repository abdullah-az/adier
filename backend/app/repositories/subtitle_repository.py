from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import List, Optional

from loguru import logger

from app.models.subtitle import SubtitleTranscript


class SubtitleRepository:
    """Persist AI generated subtitle transcripts to JSON storage."""

    def __init__(self, storage_root: str | Path) -> None:
        self.storage_root = Path(storage_root).resolve()
        self.base_dir = self.storage_root / "metadata" / "subtitles"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._locks: dict[str, asyncio.Lock] = {}
        self._lock_guard = asyncio.Lock()

    async def _get_lock(self, asset_id: str) -> asyncio.Lock:
        async with self._lock_guard:
            if asset_id not in self._locks:
                self._locks[asset_id] = asyncio.Lock()
            return self._locks[asset_id]

    def _transcript_path(self, asset_id: str) -> Path:
        safe_id = asset_id.replace("/", "_")
        return self.base_dir / f"{safe_id}.json"

    async def save_transcript(self, transcript: SubtitleTranscript) -> SubtitleTranscript:
        lock = await self._get_lock(transcript.asset_id)
        async with lock:
            path = self._transcript_path(transcript.asset_id)

            def _write() -> None:
                tmp_path = path.with_suffix(".tmp")
                with tmp_path.open("w", encoding="utf-8") as handle:
                    json.dump(transcript.model_dump(mode="json"), handle, indent=2)
                tmp_path.replace(path)

            await asyncio.to_thread(_write)
            logger.info(
                "Persisted transcript",
                asset_id=transcript.asset_id,
                project_id=transcript.project_id,
                segments=transcript.segment_count,
                cached=transcript.cached,
            )
            return transcript

    async def get_transcript(self, asset_id: str) -> Optional[SubtitleTranscript]:
        path = self._transcript_path(asset_id)
        if not path.exists():
            return None

        def _read() -> SubtitleTranscript:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            return SubtitleTranscript.model_validate(payload)

        transcript = await asyncio.to_thread(_read)
        return transcript

    async def delete_transcript(self, asset_id: str) -> None:
        lock = await self._get_lock(asset_id)
        async with lock:
            path = self._transcript_path(asset_id)
            if path.exists():
                path.unlink()
                logger.debug("Deleted transcript", asset_id=asset_id)

    async def list_project_transcripts(self, project_id: str) -> List[SubtitleTranscript]:
        def _load_all() -> List[SubtitleTranscript]:
            transcripts: List[SubtitleTranscript] = []
            for file_path in self.base_dir.glob("*.json"):
                with file_path.open("r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                try:
                    transcript = SubtitleTranscript.model_validate(payload)
                except Exception as exc:  # pragma: no cover - defensive against corrupt files
                    logger.warning(
                        "Skipping invalid transcript file",
                        path=str(file_path),
                        error=str(exc),
                    )
                    continue
                transcripts.append(transcript)
            return transcripts

        transcripts = await asyncio.to_thread(_load_all)
        return [item for item in transcripts if item.project_id == project_id]


__all__ = ["SubtitleRepository"]
