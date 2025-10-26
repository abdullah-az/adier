from __future__ import annotations

import hashlib
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from app.core.config import Settings
from app.models.subtitle import SubtitleSegment, SubtitleTranscript
from app.models.video_asset import VideoAsset
from app.repositories.subtitle_repository import SubtitleRepository
from app.repositories.video_repository import VideoAssetRepository
from app.services.exceptions import (
    AIMissingConfigurationError,
    AINonRetryableError,
    AIRetryableError,
)
from app.services.openai_client import OpenAIClient
from app.utils.ffmpeg import FFmpegError, extract_audio_track, get_video_metadata, probe_media_duration
from app.utils.storage import StorageManager


@dataclass(slots=True)
class AudioChunk:
    path: Path
    start: float
    duration: float


class TranscriptionService:
    """Coordinate audio extraction and OpenAI Whisper transcription."""

    def __init__(
        self,
        *,
        settings: Settings,
        storage_manager: StorageManager,
        video_repository: VideoAssetRepository,
        subtitle_repository: SubtitleRepository,
        openai_client: OpenAIClient,
    ) -> None:
        self.settings = settings
        self.storage_manager = storage_manager
        self.video_repository = video_repository
        self.subtitle_repository = subtitle_repository
        self.openai_client = openai_client
        self.model = settings.openai_transcription_model
        self.chunk_seconds = max(60, settings.openai_transcription_chunk_seconds)
        self.sample_rate = max(8000, settings.openai_transcription_sample_rate)

    async def transcribe_asset(
        self,
        *,
        project_id: str,
        asset_id: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        force: bool = False,
    ) -> SubtitleTranscript:
        logger.info(
            "Starting transcription",
            asset_id=asset_id,
            project_id=project_id,
            force=force,
            language=language,
        )
        asset = await self.video_repository.get(asset_id)
        if asset is None or asset.project_id != project_id:
            raise AINonRetryableError("Video asset not found for transcription", context={"asset_id": asset_id})

        request_hash = self._request_hash(language=language, prompt=prompt)
        cached = await self.subtitle_repository.get_transcript(asset_id)
        if cached and not force:
            cached.metadata.setdefault("request_hash", cached.metadata.get("request_hash", request_hash))
            if cached.metadata.get("request_hash") == request_hash:
                cached.cached = True
                logger.info(
                    "Returning cached transcript",
                    asset_id=asset_id,
                    project_id=project_id,
                    segments=cached.segment_count,
                )
                return cached

        if not self.settings.openai_api_key:
            raise AIMissingConfigurationError("OpenAI transcription requires OPENAI_API_KEY")

        video_path = Path(self.storage_manager.storage_root) / asset.relative_path
        if not video_path.exists():
            raise AINonRetryableError(
                "Video file missing from storage",
                context={"asset_id": asset_id, "path": str(video_path)},
            )

        duration = self._resolve_duration(asset, video_path)
        if duration and (asset.metadata or {}).get("duration") != duration:
            try:
                await self.video_repository.update(asset)
            except Exception as exc:  # pragma: no cover - defensive persistence
                logger.warning(
                    "Unable to persist updated video metadata",
                    asset_id=asset.id,
                    error=str(exc),
                )
        chunks, temp_dir = await self._prepare_audio_chunks(video_path, duration)

        try:
            transcript = await self._transcribe_chunks(
                asset=asset,
                chunks=chunks,
                language=language,
                prompt=prompt,
                request_hash=request_hash,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        saved = await self.subtitle_repository.save_transcript(transcript)
        logger.info(
            "Transcription completed",
            asset_id=asset_id,
            project_id=project_id,
            segments=saved.segment_count,
            duration=saved.duration,
            total_tokens=saved.usage.get("total_tokens"),
            requests=saved.usage.get("requests"),
        )
        return saved

    async def _transcribe_chunks(
        self,
        *,
        asset: VideoAsset,
        chunks: list[AudioChunk],
        language: Optional[str],
        prompt: Optional[str],
        request_hash: str,
    ) -> SubtitleTranscript:
        segments: list[SubtitleSegment] = []
        usage_totals: dict[str, float] = {
            "requests": 0,
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
        }
        transcript_text_parts: list[str] = []

        for index, chunk in enumerate(chunks):
            logger.debug(
                "Submitting audio chunk to OpenAI",
                asset_id=asset.id,
                chunk_index=index,
                start=chunk.start,
                duration=chunk.duration,
            )
            try:
                response = await self.openai_client.transcribe_audio(
                    file_path=chunk.path,
                    model=self.model,
                    language=language,
                    prompt=prompt,
                )
            except AIRetryableError:
                raise
            except AIMissingConfigurationError:
                raise
            except Exception as exc:  # pragma: no cover - defensive fallback
                raise AIRetryableError(
                    "Unexpected error during transcription",
                    context={"asset_id": asset.id, "chunk_index": index},
                ) from exc

            chunk_usage = response.get("usage") or {}
            self._merge_usage(usage_totals, chunk_usage)
            segments_data = response.get("segments") or []
            if not isinstance(segments_data, list):
                segments_data = []

            for seg in segments_data:
                start = float(seg.get("start", 0.0)) + chunk.start
                end = float(seg.get("end", max(seg.get("start", 0.0), 0.0))) + chunk.start
                text = (seg.get("text") or "").strip()
                if not text:
                    continue
                confidence = seg.get("confidence")
                if confidence is None:
                    avg_logprob = seg.get("avg_logprob")
                    if avg_logprob is not None:
                        confidence = max(0.0, min(1.0, 1.0 + float(avg_logprob)))
                segment = SubtitleSegment(
                    id=hashlib.sha1(f"{asset.id}:{len(segments)}:{start}".encode("utf-8")).hexdigest(),
                    asset_id=asset.id,
                    project_id=asset.project_id,
                    index=len(segments),
                    start=start,
                    end=end,
                    text=text,
                    confidence=confidence,
                    language=response.get("language"),
                    request_id=request_hash,
                    metadata={
                        "chunk_index": index,
                        "avg_logprob": seg.get("avg_logprob"),
                        "temperature": response.get("temperature"),
                    },
                )
                segments.append(segment)
                transcript_text_parts.append(text)

            if not segments_data:
                raw_text = (response.get("text") or "").strip()
                if raw_text:
                    transcript_text_parts.append(raw_text)

            usage_totals["requests"] += 1

        transcript = SubtitleTranscript(
            id=request_hash,
            asset_id=asset.id,
            project_id=asset.project_id,
            language=segments[0].language if segments else (language or "auto"),
            source_model=self.model,
            prompt=prompt,
            parameters={
                "language": language,
                "prompt": prompt,
                "chunk_seconds": self.chunk_seconds,
            },
            usage=usage_totals,
            text=" ".join(transcript_text_parts).strip(),
            segments=segments,
            cached=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={
                "request_hash": request_hash,
                "chunk_count": len(chunks),
                "chunk_durations": [chunk.duration for chunk in chunks],
            },
        )
        return transcript

    def _merge_usage(self, totals: dict[str, float], chunk_usage: dict[str, Any]) -> None:
        for key in ("total_tokens", "prompt_tokens", "completion_tokens"):
            try:
                value = float(chunk_usage.get(key, 0))
            except (TypeError, ValueError):  # pragma: no cover - defensive
                value = 0.0
            totals[key] = totals.get(key, 0.0) + value

    def _resolve_duration(self, asset: VideoAsset, video_path: Path) -> Optional[float]:
        duration = (asset.metadata or {}).get("duration")
        if duration and duration > 0:
            return float(duration)
        try:
            metadata = get_video_metadata(video_path)
            duration = metadata.get("duration")
            if duration:
                asset.metadata = metadata
                return float(duration)
        except FFmpegError as exc:
            logger.warning("Failed to probe video metadata for duration", asset_id=asset.id, error=str(exc))
        return None

    async def _prepare_audio_chunks(
        self,
        video_path: Path,
        duration: Optional[float],
    ) -> tuple[list[AudioChunk], Path]:
        temp_dir_path = Path(tempfile.mkdtemp(prefix="transcribe-"))
        audio_chunks: list[AudioChunk] = []

        if not duration or duration <= self.chunk_seconds:
            chunk_path = temp_dir_path / "chunk_000.wav"
            await extract_audio_track(
                video_path,
                chunk_path,
                sample_rate=self.sample_rate,
                channels=1,
            )
            actual_duration = await probe_media_duration(chunk_path)
            if actual_duration <= 0 and duration:
                actual_duration = float(duration)
            audio_chunks.append(AudioChunk(path=chunk_path, start=0.0, duration=actual_duration))
            return audio_chunks, temp_dir_path

        total = float(duration)
        start = 0.0
        index = 0
        while start < total:
            remaining = max(total - start, 0.0)
            segment_duration = min(self.chunk_seconds, remaining)
            chunk_path = temp_dir_path / f"chunk_{index:03d}.wav"
            await extract_audio_track(
                video_path,
                chunk_path,
                start=start,
                duration=segment_duration,
                sample_rate=self.sample_rate,
                channels=1,
            )
            actual_duration = await probe_media_duration(chunk_path)
            if actual_duration <= 0:
                actual_duration = segment_duration
            audio_chunks.append(AudioChunk(path=chunk_path, start=start, duration=actual_duration))
            start += segment_duration
            index += 1

        return audio_chunks, temp_dir_path

    def _request_hash(self, *, language: Optional[str], prompt: Optional[str]) -> str:
        payload = f"{self.model}:{language or 'auto'}:{prompt or ''}:{self.chunk_seconds}"
        return hashlib.sha1(payload.encode("utf-8")).hexdigest()


__all__ = ["TranscriptionService"]
