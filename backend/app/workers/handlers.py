from __future__ import annotations

import asyncio
from typing import Any, Iterable

from pydantic import ValidationError

from app.models.pipeline import TimelineCompositionRequest
from app.services.ai import AIOrchestrator, ProviderUnavailableError
from app.services.job_service import JobExecutionContext
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


def create_scene_detection_handler(orchestrator: AIOrchestrator):
    async def scene_detection(context: JobExecutionContext) -> dict[str, Any]:
        payload = context.payload or {}
        frames = payload.get("frames") or payload.get("video_frames") or []
        transcript = payload.get("transcript")

        await context.log(
            "Initialising scene detection pipeline",
            payload_keys=sorted(payload.keys()),
            provider_priority=orchestrator.get_priority(),
        )
        await _run_steps(
            context,
            [
                (12.0, "Profiling source media"),
                (32.0, "Selecting scene analysis provider"),
            ],
        )
        try:
            invocation = await orchestrator.analyze_scene(
                context.project_id,
                video_frames=frames,
                transcript=transcript,
                frame_descriptions=payload.get("frame_descriptions"),
            )
        except ProviderUnavailableError as exc:
            await context.log(
                "Scene detection providers exhausted",
                level="ERROR",
                attempts=exc.attempts,
            )
            raise

        await context.progress(88.0, message="Consolidating scene candidates")
        result = invocation.to_dict()
        await context.log(
            "Scene detection completed",
            provider=result["provider"],
            attempts=len(result["metadata"]["attempts"]),
            cost=result["cost"]["amount"],
            currency=result["cost"]["currency"],
        )
        return result

    return scene_detection


def create_transcription_handler(orchestrator: AIOrchestrator):
    async def transcribe(context: JobExecutionContext) -> dict[str, Any]:
        payload = context.payload or {}
        audio_source = payload.get("audio") or payload.get("audio_source") or payload.get("file")
        language = payload.get("language")

        if audio_source is None:
            await context.log(
                "Transcription job missing required audio payload",
                level="ERROR",
                payload=payload,
            )
            raise ValueError("Transcription job requires an 'audio' payload entry")

        await context.log(
            "Preparing transcription request",
            payload_keys=sorted(payload.keys()),
            provider_priority=orchestrator.get_priority(),
        )
        await _run_steps(
            context,
            [
                (18.0, "Preparing audio for transfer"),
                (42.0, "Selecting transcription provider"),
            ],
        )
        try:
            invocation = await orchestrator.transcribe_audio(
                context.project_id,
                audio_source=audio_source,
                language=language,
            )
        except ProviderUnavailableError as exc:
            await context.log(
                "Transcription providers exhausted",
                level="ERROR",
                attempts=exc.attempts,
            )
            raise

        await context.progress(90.0, message="Packaging transcript")
        result = invocation.to_dict()
        await context.log(
            "Transcription complete",
            provider=result["provider"],
            cost=result["cost"]["amount"],
            currency=result["cost"]["currency"],
        )
        return result

    return transcribe


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
