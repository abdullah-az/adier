from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from celery import Celery
from celery.exceptions import OperationalError as CeleryOperationalError
from sqlalchemy.orm import Session

from ..core.config import Settings, get_settings
from ..core.database import session_scope
from ..models.enums import ProcessingJobStatus, ProcessingJobType
from ..models.processing_job import ProcessingJob
from ..repositories.processing_job import ProcessingJobRepository
from ..schemas.processing_job import ProcessingJobCreate, ProcessingJobUpdate
from .celery_app import celery_app

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ProcessingJobLifecycle:
    """Helper for enqueuing and updating background processing jobs."""

    settings: Settings = get_settings()
    celery: Celery = celery_app
    task_name: str = "backend.app.workers.tasks.process_job"

    @classmethod
    def enqueue(
        cls,
        job_type: ProcessingJobType,
        payload: dict[str, Any],
        *,
        clip_version_id: str | None = None,
        priority: int = 0,
        queue_name: str | None = None,
    ) -> ProcessingJob:
        queue = queue_name or cls.settings.queue_default_name

        with session_scope() as session:
            repository = ProcessingJobRepository(session)
            job = repository.create(
                ProcessingJobCreate(
                    clip_version_id=clip_version_id,
                    job_type=job_type,
                    status=ProcessingJobStatus.PENDING,
                    queue_name=queue,
                    priority=priority,
                    payload=payload,
                )
            )
            job_id = job.id

        try:
            async_result = cls.celery.send_task(
                cls.task_name,
                kwargs={"job_id": job_id},
                queue=queue,
                priority=priority,
            )
        except CeleryOperationalError as exc:
            error_message = f"Queue connection error: {exc}"
            logger.exception("Queue connection error while enqueueing job", extra={"job_id": job_id})
            cls.mark_failed(job_id, error_message)
            raise RuntimeError(error_message) from exc
        except Exception as exc:  # pragma: no cover - unexpected failure
            error_message = f"Failed to enqueue processing job: {exc}"
            logger.exception("Unexpected error while enqueueing job", extra={"job_id": job_id})
            cls.mark_failed(job_id, error_message)
            raise

        cls.mark_queued(job_id, queue_name=queue, task_id=async_result.id)
        job = cls.get_job(job_id)
        if job is None:  # pragma: no cover - defensive programming
            raise RuntimeError(f"Processing job {job_id} could not be retrieved after enqueueing.")

        return job

    @classmethod
    def get_job(cls, job_id: str) -> Optional[ProcessingJob]:
        with session_scope() as session:
            repository = ProcessingJobRepository(session)
            return repository.get(job_id)

    @classmethod
    def mark_queued(
        cls,
        job_id: str,
        *,
        queue_name: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> ProcessingJob:
        update_payload: dict[str, Any] = {}
        if task_id is not None:
            update_payload["task_id"] = task_id
        return cls._update_job(
            job_id,
            status=ProcessingJobStatus.QUEUED,
            queue_name=queue_name,
            result_updates=update_payload,
        )

    @classmethod
    def mark_started(cls, job_id: str) -> ProcessingJob:
        return cls._update_job(
            job_id,
            status=ProcessingJobStatus.IN_PROGRESS,
            started_at=_now(),
        )

    @classmethod
    def mark_progress(
        cls,
        job_id: str,
        *,
        progress: Optional[float] = None,
        message: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ProcessingJob:
        updates: dict[str, Any] = {}
        if progress is not None:
            updates["progress"] = progress
        if message is not None:
            updates.setdefault("updates", [])
        result_updates: dict[str, Any] = {}

        if metadata:
            result_updates.update(metadata)

        if progress is not None:
            result_updates["progress"] = progress

        if message is not None:
            result_updates.setdefault("log", [])
            result_updates["log"].append({"timestamp": _now().isoformat(), "message": message})

        return cls._update_job(job_id, result_updates=result_updates)

    @classmethod
    def mark_completed(
        cls,
        job_id: str,
        result_payload: Optional[dict[str, Any]] = None,
    ) -> ProcessingJob:
        return cls._update_job(
            job_id,
            status=ProcessingJobStatus.COMPLETED,
            completed_at=_now(),
            result_updates=result_payload,
        )

    @classmethod
    def mark_failed(
        cls,
        job_id: str,
        error_message: str,
        *,
        result_payload: Optional[dict[str, Any]] = None,
    ) -> ProcessingJob:
        return cls._update_job(
            job_id,
            status=ProcessingJobStatus.FAILED,
            completed_at=_now(),
            error_message=error_message,
            result_updates=result_payload,
        )

    @classmethod
    def _update_job(
        cls,
        job_id: str,
        *,
        status: Optional[ProcessingJobStatus] = None,
        queue_name: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
        result_updates: Optional[dict[str, Any]] = None,
    ) -> ProcessingJob:
        with session_scope() as session:
            repository = ProcessingJobRepository(session)
            job = repository.get(job_id)
            if job is None:
                raise RuntimeError(f"Processing job {job_id} not found")

            update_data: dict[str, Any] = {}
            if status is not None:
                update_data["status"] = status
            if queue_name is not None:
                update_data["queue_name"] = queue_name
            if started_at is not None:
                update_data["started_at"] = started_at
            if completed_at is not None:
                update_data["completed_at"] = completed_at
            if error_message is not None:
                update_data["error_message"] = error_message

            if result_updates is not None:
                merged_result = dict(job.result_payload or {})
                logs = result_updates.pop("log", []) if "log" in result_updates else []
                if logs:
                    existing_logs = list(merged_result.get("log", []))
                    existing_logs.extend(logs)
                    merged_result["log"] = existing_logs
                merged_result.update(result_updates)
                update_data["result_payload"] = merged_result

            updated_job = repository.update(job, ProcessingJobUpdate(**update_data))

            logger.debug(
                "Processing job updated",
                extra={
                    "job_id": job_id,
                    "status": updated_job.status.value,
                    "queue_name": updated_job.queue_name,
                },
            )
            return updated_job


__all__ = ["ProcessingJobLifecycle"]
