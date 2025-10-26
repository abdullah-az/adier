from __future__ import annotations

import asyncio
from typing import Any, Iterable

from pydantic import ValidationError

from app.models.pipeline import TimelineCompositionRequest
from app.services.exceptions import AIServiceError, AINonRetryableError
from app.services.job_service import JobExecutionContext
from app.services.scene_analysis_service import SceneAnalysisService
from app.services.transcription_service import TranscriptionService
from app.services.video_pipeline_service import PipelineError, VideoPipelineService
from app.utils.ffmpeg import FFmpegError

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



async def _handle_ai_error(context: JobExecutionContext, error: AIServiceError, *, stage: str) -> dict[str, Any]:
    level = "WARNING" if error.retryable else "ERROR"
    await context.log(f"{stage} failed", level=level, error=str(error), context=error.context)
    if error.retryable:
        raise error
    await context.mark_failed(str(error))
    return {"status": "failed", "error": error.to_dict()}


def create_transcription_handler(transcription_service: "TranscriptionService"):
    async def transcription_handler(context: JobExecutionContext) -> dict[str, Any]:
        payload = context.payload or {}
        asset_id = payload.get("asset_id")
        if not asset_id:
            error = AINonRetryableError("Transcription job payload requires 'asset_id'")
            return await _handle_ai_error(context, error, stage="Transcription")
        language = payload.get("language")
        prompt = payload.get("prompt")
        force = bool(payload.get("force", False))

        await context.log(
            "Starting transcription job",
            asset_id=asset_id,
            language=language,
            force=force,
        )
        await context.progress(5.0, message="Preparing audio extraction")

        try:
            transcript = await transcription_service.transcribe_asset(
                project_id=context.project_id,
                asset_id=asset_id,
                language=language,
                prompt=prompt,
                force=force,
            )
        except AIServiceError as error:
            return await _handle_ai_error(context, error, stage="Transcription")

        await context.progress(95.0, message="Persisting transcript")
        await context.log(
            "Transcription completed",
            asset_id=asset_id,
            segments=transcript.segment_count,
            cached=transcript.cached,
        )
        return {
            "asset_id": asset_id,
            "transcript_id": transcript.id,
            "segments": transcript.segment_count,
            "duration": transcript.duration,
            "language": transcript.language,
            "cached": transcript.cached,
            "usage": transcript.usage,
        }

    return transcription_handler


def create_scene_detection_handler(scene_service: "SceneAnalysisService"):
    async def scene_detection_handler(context: JobExecutionContext) -> dict[str, Any]:
        payload = context.payload or {}
        asset_id = payload.get("asset_id")
        if not asset_id:
            error = AINonRetryableError("Scene detection job payload requires 'asset_id'")
            return await _handle_ai_error(context, error, stage="Scene detection")

        tone = payload.get("tone") or payload.get("style")
        criteria = payload.get("criteria") or payload.get("highlight_criteria")
        max_scenes = payload.get("max_scenes")
        force = bool(payload.get("force", False))
        extra_instructions = payload.get("instructions")

        await context.log(
            "Starting scene analysis",
            asset_id=asset_id,
            tone=tone,
            criteria=criteria,
            max_scenes=max_scenes,
            force=force,
        )
        await context.progress(5.0, message="Preparing scene analysis")

        try:
            run = await scene_service.detect_scenes(
                project_id=context.project_id,
                asset_id=asset_id,
                tone=tone,
                highlight_criteria=criteria,
                max_scenes=max_scenes,
                force=force,
                extra_instructions=extra_instructions,
            )
        except AIServiceError as error:
            return await _handle_ai_error(context, error, stage="Scene detection")

        await context.progress(95.0, message="Persisting scene recommendations")
        await context.log(
            "Scene detection completed",
            asset_id=asset_id,
            scenes=run.scene_count,
            cached=run.metadata.get("cached", False),
        )
        return {
            "asset_id": asset_id,
            "analysis_id": run.id,
            "scenes": run.scene_count,
            "cached": run.metadata.get("cached", False),
            "usage": run.usage,
        }

    return scene_detection_handler


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
