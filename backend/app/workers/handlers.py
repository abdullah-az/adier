from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Iterable, Optional

from pydantic import ValidationError

from app.models.pipeline import TimelineCompositionRequest
from app.repositories.video_repository import VideoAssetRepository
from app.services.ai.exceptions import AIProviderError
from app.services.ai.manager import AIManager
from app.services.job_service import JobExecutionContext
from app.services.video_pipeline_service import PipelineError, VideoPipelineService
from app.utils.ffmpeg import FFmpegError
from app.utils.storage import StorageManager

_STEP_DELAY_SECONDS = 0.25


async def _run_steps(context: JobExecutionContext, steps: Iterable[tuple[float, str]]) -> None:
    for progress, message in steps:
        await context.progress(progress, message=message)
        await asyncio.sleep(_STEP_DELAY_SECONDS)


async def ingest_handler(context: JobExecutionContext) -> dict[str, Any]:
    await context.log("Validating ingest request", payload=context.payload)
    await _run_steps(
        context,
        [
            (10.0, "Validating source media"),
            (35.0, "Copying media to staging"),
            (60.0, "Extracting technical metadata"),
            (85.0, "Registering asset in catalog"),
        ],
    )
    await context.log("Ingest processing complete")
    return {
        "asset_id": context.payload.get("asset_id"),
        "checksum": context.payload.get("checksum"),
        "notes": "Ingest pipeline completed",
    }


def create_scene_detection_handler(
    ai_manager: AIManager,
    storage_manager: StorageManager,
    video_repository: VideoAssetRepository,
):
    async def handler(context: JobExecutionContext) -> dict[str, Any]:
        payload = context.payload or {}
        await context.log("Initialising scene detection pipeline", payload=payload)

        video_path = await _resolve_media_path(
            context.project_id,
            payload,
            storage_manager,
            video_repository,
            fallback_keys=("video_path", "path"),
        )

        preferred = _normalise_preferred(payload.get("preferred_providers") or payload.get("provider"))
        options = payload.get("analysis_options") or payload.get("options") or {}
        if not isinstance(options, dict):
            options = {}

        await context.progress(20.0, message="Preparing frame samples")
        try:
            result = await ai_manager.run_scene_detection(
                context.project_id,
                video_path,
                preferred_providers=preferred,
                **options,
            )
        except AIProviderError as exc:
            await context.log("Scene detection failed", level="ERROR", error=str(exc))
            raise

        summary = result.get("provider", {})
        await context.progress(92.0, message="Aggregating scene segments")
        await context.log(
            "Scene detection completed",
            provider=summary.get("name"),
            attempts=summary.get("attempts"),
            scenes=len(result.get("scenes", [])),
        )
        return result

    return handler


def create_transcription_handler(
    ai_manager: AIManager,
    storage_manager: StorageManager,
    video_repository: VideoAssetRepository,
):
    async def handler(context: JobExecutionContext) -> dict[str, Any]:
        payload = context.payload or {}
        await context.log("Preparing transcription request", payload=payload)

        media_path = await _resolve_media_path(
            context.project_id,
            payload,
            storage_manager,
            video_repository,
            fallback_keys=("audio_path", "path", "video_path"),
        )

        preferred = _normalise_preferred(payload.get("preferred_providers") or payload.get("provider"))
        language = payload.get("language")
        options = payload.get("transcription_options") or payload.get("options") or {}
        if not isinstance(options, dict):
            options = {}

        await context.progress(25.0, message="Uploading audio to provider")
        try:
            result = await ai_manager.run_transcription(
                context.project_id,
                media_path,
                preferred_providers=preferred,
                language=language,
                **options,
            )
        except AIProviderError as exc:
            await context.log("Transcription failed", level="ERROR", error=str(exc))
            raise

        summary = result.get("provider", {})
        await context.progress(94.0, message="Finalising transcript")
        await context.log(
            "Transcription complete",
            provider=summary.get("name"),
            attempts=summary.get("attempts"),
            language=result.get("language"),
        )
        return result

    return handler


def create_export_handler(pipeline_service: VideoPipelineService):
    async def export_handler(context: JobExecutionContext) -> dict[str, Any]:
        await context.log("Starting export pipeline", payload=context.payload)
        payload = context.payload or {}
        timeline_payload = payload.get("timeline") or payload
        try:
            request = TimelineCompositionRequest.model_validate(timeline_payload)
        except ValidationError as exc:
            raise PipelineError(f"Invalid timeline payload: {exc}") from exc

        async def log_callback(message: str, details: dict[str, Any]) -> None:
            await context.log(message, **details)

        async def progress_callback(value: float, message: str) -> None:
            await context.progress(value, message=message)

        try:
            result = await pipeline_service.compose_timeline(
                context.project_id,
                request,
                log=log_callback,
                progress=progress_callback,
            )
        except (PipelineError, FFmpegError) as exc:
            await context.log("Export pipeline failed", level="ERROR", error=str(exc))
            raise

        await context.log(
            "Export pipeline complete",
            exports=len(result.exports),
            proxy=bool(result.proxy),
        )
        return result.model_dump()

    return export_handler


async def _resolve_media_path(
    project_id: str,
    payload: dict[str, Any],
    storage_manager: StorageManager,
    video_repository: VideoAssetRepository,
    *,
    fallback_keys: tuple[str, ...],
) -> Path:
    path_candidates = [payload.get(key) for key in fallback_keys if payload.get(key)]
    relative_path = payload.get("relative_path")
    asset_id = (
        payload.get("asset_id")
        or payload.get("video_asset_id")
        or payload.get("audio_asset_id")
    )

    if path_candidates:
        resolved = _coerce_path(path_candidates[0], storage_manager)
        if resolved.exists():
            return resolved

    if relative_path:
        resolved = _coerce_path(relative_path, storage_manager)
        if resolved.exists():
            return resolved

    if asset_id:
        asset = await video_repository.get(asset_id)
        if asset is None or asset.project_id != project_id:
            raise PipelineError(f"Asset '{asset_id}' not found for project '{project_id}'")
        resolved = (storage_manager.storage_root / asset.relative_path).resolve()
        if not resolved.exists():
            raise PipelineError(f"Asset file missing at '{resolved}'")
        return resolved

    raise PipelineError("Media path resolution failed - provide a path or asset identifier")


def _coerce_path(path_value: str | Path, storage_manager: StorageManager) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = (storage_manager.storage_root / path).resolve()
    return path


def _normalise_preferred(value: Optional[Any]) -> Optional[list[str]]:
    if value is None:
        return None
    if isinstance(value, str):
        if "," in value:
            return [item.strip() for item in value.split(",") if item.strip()]
        return [value.strip()] if value.strip() else None
    if isinstance(value, Iterable):
        items = [str(item).strip() for item in value if str(item).strip()]
        return items or None
    return None
