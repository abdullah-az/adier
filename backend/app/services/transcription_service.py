from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from loguru import logger

from app.core.config import Settings
from app.models.transcription import SubtitleSegment, Transcript
from app.repositories.transcript_repository import TranscriptRepository
from app.repositories.video_repository import VideoAssetRepository
from app.services.openai_service import OpenAIConfigurationError, OpenAIService
from app.utils.ffmpeg import (
    FFmpegError,
    extract_audio_track,
    get_media_duration,
    split_audio_into_chunks,
)
from app.utils.storage import StorageManager
from app.services.job_service import JobExecutionContext


class TranscriptionService:
    """Coordinates audio extraction, transcription calls, and persistence."""

    def __init__(
        self,
        *,
        settings: Settings,
        storage_manager: StorageManager,
        video_repository: VideoAssetRepository,
        transcript_repository: TranscriptRepository,
        openai_service: OpenAIService,
    ) -> None:
        self.settings = settings
        self.storage_manager = storage_manager
        self.video_repository = video_repository
        self.transcript_repository = transcript_repository
        self.openai_service = openai_service

        self.chunk_duration_seconds = float(getattr(settings, "transcription_chunk_duration", 600))
        self.chunk_overlap_seconds = float(getattr(settings, "transcription_chunk_overlap", 0.0))
        self.audio_format = getattr(settings, "transcription_audio_format", "wav")
        self.audio_sample_rate = int(getattr(settings, "transcription_sample_rate", 16000))
        self.audio_channels = int(getattr(settings, "transcription_channels", 1))
        self.whisper_model = getattr(settings, "openai_whisper_model", "gpt-4o-mini-transcribe")
        self.whisper_fallback_path = getattr(settings, "whisper_cli_path", None)
        self.whisper_fallback_model = getattr(settings, "whisper_cli_model", "base.en")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def run_transcription_job(self, context: JobExecutionContext) -> Dict[str, Any]:
        payload = context.payload
        asset_id = payload.get("asset_id")
        if not asset_id:
            raise ValueError("Transcription job payload missing 'asset_id'")

        force = bool(payload.get("force", False))
        requested_language = payload.get("language")
        requested_chunk_duration = payload.get("chunk_duration")
        if requested_chunk_duration:
            try:
                chunk_duration = max(60.0, float(requested_chunk_duration))
            except (TypeError, ValueError):
                chunk_duration = self.chunk_duration_seconds
        else:
            chunk_duration = self.chunk_duration_seconds

        await context.progress(2.0, message="Fetching asset metadata")
        asset = await self.video_repository.get(asset_id)
        if asset is None or asset.project_id != context.project_id:
            raise ValueError("Video asset not found for transcription")

        existing = await self.transcript_repository.get_by_asset(asset_id)
        if existing and not force:
            await context.log(
                "Transcript already exists; skipping new transcription",
                transcript_id=existing.id,
            )
            await context.progress(100.0, message="Transcript already available")
            return {
                "asset_id": asset_id,
                "transcript_id": existing.id,
                "language": existing.language,
                "segments": len(existing.segments),
                "cached": True,
            }

        video_path = Path(self.storage_manager.storage_root) / asset.relative_path
        audio_dir = self.storage_manager.project_category_path(asset.project_id, "audio")
        audio_path = audio_dir / f"{asset.id}.{self.audio_format}"

        await context.progress(5.0, message="Extracting audio track")
        try:
            await extract_audio_track(
                video_path,
                audio_path,
                sample_rate=self.audio_sample_rate,
                channels=self.audio_channels,
                audio_format=self.audio_format,
            )
        except FFmpegError as exc:
            raise RuntimeError(f"Failed to extract audio: {exc}") from exc

        await context.progress(15.0, message="Determining audio duration")
        try:
            audio_duration = await get_media_duration(audio_path)
        except FFmpegError:
            audio_duration = 0.0

        chunk_paths: List[Path]
        if audio_duration and audio_duration <= chunk_duration:
            chunk_paths = [audio_path]
        else:
            chunk_dir = audio_dir / f"{asset.id}_chunks"
            await context.log(
                "Segmenting audio for long-form transcription",
                chunk_duration=chunk_duration,
            )
            try:
                chunk_paths = await split_audio_into_chunks(
                    audio_path,
                    chunk_dir,
                    chunk_duration=chunk_duration,
                )
            except FFmpegError as exc:
                raise RuntimeError(f"Failed to split audio into chunks: {exc}") from exc

        await context.progress(25.0, message=f"Dispatching {len(chunk_paths)} chunk(s) for transcription")

        segments: List[SubtitleSegment] = []
        accumulated_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        detected_language: Optional[str] = None

        offset_seconds = 0.0
        for idx, chunk_file in enumerate(chunk_paths):
            chunk_label = f"Chunk {idx + 1}/{len(chunk_paths)}"
            await context.log("Submitting audio chunk to Whisper", chunk=chunk_label, path=str(chunk_file))

            try:
                response = await self.openai_service.transcribe_audio(
                    file_path=chunk_file,
                    model=self.whisper_model,
                    language=requested_language,
                )
                raw_segments = getattr(response, "segments", None)
                if detected_language is None:
                    detected_language = getattr(response, "language", None) or requested_language
                usage = self._extract_usage(getattr(response, "usage", None))
            except OpenAIConfigurationError as exc:
                await context.log("OpenAI not configured; attempting whisper.cpp fallback", level="WARNING")
                response, raw_segments, usage = await self._transcribe_with_whisper_cli(
                    chunk_file,
                    idx,
                    requested_language,
                )
                if detected_language is None:
                    detected_language = response.get("language", requested_language)
            except Exception as exc:  # pragma: no cover - depends on networked API
                raise RuntimeError(f"OpenAI transcription failed: {exc}") from exc

            chunk_segments = self._parse_segments(
                raw_segments=raw_segments,
                chunk_index=idx,
                existing_count=len(segments),
                offset_seconds=offset_seconds,
            )
            segments.extend(chunk_segments)

            for key, value in usage.items():
                if value is None:
                    continue
                accumulated_usage[key] = accumulated_usage.get(key, 0) + int(value)

            try:
                chunk_duration_seconds = await get_media_duration(chunk_file)
            except FFmpegError:
                chunk_duration_seconds = 0.0
            offset_seconds += chunk_duration_seconds or chunk_duration
            if self.chunk_overlap_seconds and idx < len(chunk_paths) - 1:
                offset_seconds = max(0.0, offset_seconds - self.chunk_overlap_seconds)

            progress = 25.0 + ((idx + 1) / len(chunk_paths)) * 55.0
            await context.progress(progress, message=f"Processed {chunk_label}", tokens=usage)

        if not segments:
            raise RuntimeError("Transcription completed but no segments were produced")

        segments.sort(key=lambda item: item.index)
        full_text = " ".join(segment.text.strip() for segment in segments).strip()
        transcript = Transcript(
            id=str(uuid4()),
            project_id=asset.project_id,
            asset_id=asset.id,
            language=detected_language or requested_language or "unknown",
            segments=segments,
            full_text=full_text,
            duration_seconds=offset_seconds,
            usage=accumulated_usage,
            metadata={
                "chunk_count": len(chunk_paths),
                "chunk_duration": chunk_duration,
                "audio_format": self.audio_format,
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        await self.transcript_repository.save(transcript, replace_existing=True)

        asset.metadata.setdefault("analysis", {})["transcript_id"] = transcript.id
        asset.metadata["language"] = transcript.language
        asset.metadata.setdefault("analysis", {})["transcript"] = {
            "segments": len(segments),
            "generated_at": transcript.created_at.isoformat(),
        }
        asset.updated_at = datetime.utcnow()
        await self.video_repository.update(asset)

        await context.progress(100.0, message="Transcript stored", transcript_id=transcript.id)
        await context.log(
            "Transcription completed",
            transcript_id=transcript.id,
            segments=len(segments),
            language=transcript.language,
            usage=accumulated_usage,
        )

        return {
            "asset_id": asset.id,
            "transcript_id": transcript.id,
            "segments": len(segments),
            "language": transcript.language,
            "usage": accumulated_usage,
            "chunk_count": len(chunk_paths),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    async def _transcribe_with_whisper_cli(
        self,
        audio_path: Path,
        chunk_index: int,
        language: Optional[str],
    ) -> tuple[Dict[str, Any], Any, Dict[str, Any]]:
        if not self.whisper_fallback_path:
            raise OpenAIConfigurationError("Whisper CLI fallback is not configured")

        output_dir = audio_path.parent
        command = [
            self.whisper_fallback_path,
            str(audio_path),
            "--output_format",
            "json",
            "--output_dir",
            str(output_dir),
            "--model",
            self.whisper_fallback_model,
        ]
        if language:
            command.extend(["--language", language])

        logger.info("Invoking whisper.cpp fallback", command=command)
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            logger.error(
                "whisper.cpp fallback failed",
                chunk_index=chunk_index,
                stdout=stdout.decode(errors="ignore"),
                stderr=stderr.decode(errors="ignore"),
            )
            raise RuntimeError("whisper.cpp fallback failed")

        output_file = audio_path.with_suffix(".json")
        if not output_file.exists():
            raise RuntimeError("Expected whisper.cpp JSON output was not produced")

        with output_file.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        segments = payload.get("segments") or []
        usage = {
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "fallback": "whisper.cpp",
        }
        return payload, segments, usage

    def _parse_segments(
        self,
        *,
        raw_segments: Any,
        chunk_index: int,
        existing_count: int,
        offset_seconds: float,
    ) -> List[SubtitleSegment]:
        parsed: List[SubtitleSegment] = []
        if not raw_segments:
            return parsed

        def _extract(segment_obj: Any, key: str, default: Any = None) -> Any:
            if isinstance(segment_obj, dict):
                return segment_obj.get(key, default)
            return getattr(segment_obj, key, default)

        for idx, segment in enumerate(raw_segments):
            try:
                start = float(_extract(segment, "start", 0.0)) + offset_seconds
                end = float(_extract(segment, "end", start)) + offset_seconds
            except (TypeError, ValueError):
                start = offset_seconds
                end = offset_seconds

            if end < start:
                end = start

            text = str(_extract(segment, "text", "")).strip()
            confidence = _extract(segment, "confidence", None)
            parsed.append(
                SubtitleSegment(
                    index=existing_count + idx,
                    start_seconds=round(start, 3),
                    end_seconds=round(end, 3),
                    start_timecode=self._format_timecode(start),
                    end_timecode=self._format_timecode(end),
                    text=text,
                    confidence=float(confidence) if confidence is not None else None,
                    metadata={
                        "chunk_index": chunk_index,
                    },
                )
            )
        return parsed

    def _extract_usage(self, usage: Any) -> Dict[str, Optional[int]]:
        if usage is None:
            return {"input_tokens": None, "output_tokens": None, "total_tokens": None}
        return {
            "input_tokens": getattr(usage, "input_tokens", None),
            "output_tokens": getattr(usage, "output_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
        }

    def _format_timecode(self, seconds: float) -> str:
        total_milliseconds = int(round(seconds * 1000))
        hours, remainder = divmod(total_milliseconds, 3600_000)
        minutes, remainder = divmod(remainder, 60_000)
        secs, millis = divmod(remainder, 1000)
        return f"{hours:02}:{minutes:02}:{secs:02}.{millis:03}"
