from __future__ import annotations

import logging
import time
from typing import Any

from celery import Task
from celery.exceptions import Retry

from ..core.logging import configure_logging
from ..models.enums import ProcessingJobType
from .celery_app import celery_app
from .job_manager import ProcessingJobLifecycle

logger = logging.getLogger(__name__)


class ProcessingTask(Task):
    """Base task for processing jobs with standardized error handling."""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        job_id = kwargs.get("job_id")
        if job_id:
            error_message = f"Task failed: {type(exc).__name__}: {str(exc)}"
            logger.exception("Processing task failed", extra={"job_id": job_id, "task_id": task_id})
            ProcessingJobLifecycle.mark_failed(job_id, error_message)


@celery_app.task(base=ProcessingTask, name="backend.app.workers.tasks.process_job", bind=True)
def process_job(self: Task, job_id: str) -> dict[str, Any]:
    """
    Main task dispatcher that processes jobs based on their type.
    
    Args:
        job_id: The ID of the ProcessingJob to execute
        
    Returns:
        Result payload dictionary
    """
    from ..core.config import get_settings
    settings = get_settings()
    configure_logging(settings)

    logger.info("Starting processing job", extra={"job_id": job_id, "task_id": self.request.id})

    job = ProcessingJobLifecycle.get_job(job_id)
    if job is None:
        error_msg = f"Processing job {job_id} not found"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    ProcessingJobLifecycle.mark_started(job_id)

    try:
        if job.job_type == ProcessingJobType.INGEST:
            result = _process_ingest(job_id, job.payload)
        elif job.job_type == ProcessingJobType.TRANSCRIBE:
            result = _process_transcribe(job_id, job.payload)
        elif job.job_type == ProcessingJobType.GENERATE_CLIP:
            result = _process_generate_clip(job_id, job.payload)
        elif job.job_type == ProcessingJobType.RENDER:
            result = _process_render(job_id, job.payload)
        elif job.job_type == ProcessingJobType.EXPORT:
            result = _process_export(job_id, job.payload)
        else:
            raise ValueError(f"Unknown job type: {job.job_type}")

        ProcessingJobLifecycle.mark_completed(job_id, result)
        logger.info("Processing job completed", extra={"job_id": job_id})
        return result

    except Retry:
        raise
    except Exception as exc:
        error_message = f"{type(exc).__name__}: {str(exc)}"
        logger.exception("Processing job failed", extra={"job_id": job_id})
        ProcessingJobLifecycle.mark_failed(job_id, error_message)
        raise


def _process_ingest(job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Demo video ingest processing - simulates analyzing and extracting metadata."""
    logger.info("Processing video ingest", extra={"job_id": job_id, "payload": payload})
    
    source_path = payload.get("source_path", "unknown")
    
    for i, step in enumerate(["Validating video", "Extracting metadata", "Generating thumbnails"], start=1):
        ProcessingJobLifecycle.mark_progress(
            job_id,
            progress=i / 3,
            message=f"{step}...",
        )
        time.sleep(1)
    
    return {
        "source_path": source_path,
        "duration_seconds": 120.5,
        "resolution": "1920x1080",
        "fps": 30,
        "codec": "h264",
        "thumbnails_generated": 5,
    }


def _process_transcribe(job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Demo transcription processing - simulates audio transcription."""
    logger.info("Processing transcription", extra={"job_id": job_id, "payload": payload})
    
    media_asset_id = payload.get("media_asset_id", "unknown")
    
    for i, step in enumerate(["Extracting audio", "Sending to transcription service", "Processing results"], start=1):
        ProcessingJobLifecycle.mark_progress(
            job_id,
            progress=i / 3,
            message=f"{step}...",
        )
        time.sleep(1)
    
    return {
        "media_asset_id": media_asset_id,
        "transcript": "This is a demo transcript of the video content.",
        "word_count": 42,
        "language": "en",
    }


def _process_generate_clip(job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Demo clip generation - simulates AI-powered clip generation."""
    logger.info("Processing clip generation", extra={"job_id": job_id, "payload": payload})
    
    source_id = payload.get("source_id", "unknown")
    
    steps = [
        "Analyzing video content",
        "Identifying key moments",
        "Applying AI scoring",
        "Generating clip suggestions",
    ]
    
    for i, step in enumerate(steps, start=1):
        ProcessingJobLifecycle.mark_progress(
            job_id,
            progress=i / len(steps),
            message=f"{step}...",
        )
        time.sleep(1)
    
    return {
        "source_id": source_id,
        "clips_generated": 3,
        "clips": [
            {"start": 10.0, "end": 25.0, "score": 0.95},
            {"start": 45.0, "end": 60.0, "score": 0.88},
            {"start": 90.0, "end": 105.0, "score": 0.82},
        ],
    }


def _process_render(job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Demo render processing - simulates video rendering."""
    logger.info("Processing render", extra={"job_id": job_id, "payload": payload})
    
    clip_version_id = payload.get("clip_version_id", "unknown")
    
    for progress in [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]:
        ProcessingJobLifecycle.mark_progress(
            job_id,
            progress=progress,
            message=f"Rendering: {int(progress * 100)}%",
        )
        time.sleep(0.5)
    
    return {
        "clip_version_id": clip_version_id,
        "output_path": f"/storage/rendered/{clip_version_id}.mp4",
        "file_size_bytes": 5242880,
        "duration_seconds": 15.0,
    }


def _process_export(job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Demo export processing - simulates video export."""
    logger.info("Processing export", extra={"job_id": job_id, "payload": payload})
    
    clip_id = payload.get("clip_id", "unknown")
    export_format = payload.get("format", "mp4")
    
    for i, step in enumerate(["Preparing export", "Encoding video", "Finalizing"], start=1):
        ProcessingJobLifecycle.mark_progress(
            job_id,
            progress=i / 3,
            message=f"{step}...",
        )
        time.sleep(1)
    
    return {
        "clip_id": clip_id,
        "format": export_format,
        "export_path": f"/storage/exports/{clip_id}.{export_format}",
        "file_size_bytes": 10485760,
    }


__all__ = ["process_job"]
