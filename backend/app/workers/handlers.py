from __future__ import annotations

import asyncio
from typing import Any, Callable, Iterable

from app.services.job_service import JobExecutionContext
from app.services.scene_detection_service import SceneDetectionService
from app.services.transcription_service import TranscriptionService

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


def create_scene_detection_handler(service: SceneDetectionService) -> Callable[[JobExecutionContext], Any]:
    async def handler(context: JobExecutionContext) -> dict[str, Any]:
        await context.log("Starting scene detection pipeline", payload=context.payload)
        result = await service.run_scene_detection_job(context)
        return result

    return handler


def create_transcription_handler(service: TranscriptionService) -> Callable[[JobExecutionContext], Any]:
    async def handler(context: JobExecutionContext) -> dict[str, Any]:
        await context.log("Starting transcription pipeline", payload=context.payload)
        result = await service.run_transcription_job(context)
        return result

    return handler


async def export_handler(context: JobExecutionContext) -> dict[str, Any]:
    await context.log("Starting export job")
    await _run_steps(
        context,
        [
            (20.0, "Composing timeline"),
            (45.0, "Rendering video"),
            (65.0, "Muxing audio"),
            (90.0, "Finalizing package"),
        ],
    )
    await context.log("Export finished")
    return {
        "output_path": context.payload.get("output_path", "exports/output.mp4"),
        "format": context.payload.get("format", "mp4"),
    }
