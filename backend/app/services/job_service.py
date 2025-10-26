from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, Optional, TYPE_CHECKING, Union
from uuid import uuid4

from loguru import logger

from app.models.job import Job, JobStatus
from app.repositories.job_repository import JobRepository

if TYPE_CHECKING:
    from app.workers.job_queue import JobQueue


JobPayload = Dict[str, Any]
JobResult = Dict[str, Any]
JobHandler = Callable[["JobExecutionContext"], Awaitable[Optional[JobResult]]]


class JobEventManager:
    """Manage subscriptions for job update events."""

    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue[dict[str, Any]]]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, job_id: str) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=1)
        async with self._lock:
            self._subscribers.setdefault(job_id, set()).add(queue)
        return queue

    async def unsubscribe(self, job_id: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        async with self._lock:
            subscribers = self._subscribers.get(job_id)
            if not subscribers:
                return
            subscribers.discard(queue)
            if not subscribers:
                self._subscribers.pop(job_id, None)

    async def publish(self, job: Job) -> None:
        payload = job.model_dump(mode="json")
        async with self._lock:
            subscribers = list(self._subscribers.get(job.id, set()))
        for queue in subscribers:
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:  # pragma: no cover - defensive
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:  # pragma: no cover - defensive
                    pass
                queue.put_nowait(payload)


class JobService:
    """High level service orchestrating job lifecycle and persistence."""

    def __init__(
        self,
        repository: JobRepository,
        *,
        default_max_attempts: int = 1,
        default_retry_delay: float = 0.0,
    ) -> None:
        self.repository = repository
        self.default_max_attempts = max(1, default_max_attempts)
        self.default_retry_delay = max(0.0, float(default_retry_delay))
        self._handlers: dict[str, JobHandler] = {}
        self._events = JobEventManager()
        self._queue: Optional["JobQueue"] = None

    def attach_queue(self, queue: "JobQueue") -> None:
        self._queue = queue

    def _normalize_max_attempts(self, value: Optional[int]) -> int:
        if value is None:
            return self.default_max_attempts
        return max(1, value)

    def _normalize_retry_delay(self, value: Optional[float]) -> float:
        if value is None:
            return self.default_retry_delay
        try:
            numeric = float(value)
        except (TypeError, ValueError):  # pragma: no cover - defensive guard
            return self.default_retry_delay
        return max(0.0, numeric)

    def register_handler(self, job_type: str, handler: JobHandler) -> None:
        self._handlers[job_type] = handler
        logger.debug("Registered job handler", job_type=job_type)

    def unregister_handler(self, job_type: str) -> None:
        self._handlers.pop(job_type, None)
        logger.debug("Unregistered job handler", job_type=job_type)

    def get_handler(self, job_type: str) -> Optional[JobHandler]:
        return self._handlers.get(job_type)

    async def create_job(
        self,
        project_id: str,
        job_type: str,
        payload: Optional[JobPayload] = None,
        *,
        max_attempts: Optional[int] = None,
        retry_delay_seconds: Optional[float] = None,
    ) -> Job:
        normalized_max_attempts = self._normalize_max_attempts(max_attempts)
        normalized_retry_delay = self._normalize_retry_delay(retry_delay_seconds)
        job = Job(
            id=str(uuid4()),
            project_id=project_id,
            job_type=job_type,
            payload=payload or {},
            status=JobStatus.QUEUED,
            progress=0.0,
            attempts=0,
            max_attempts=normalized_max_attempts,
            retry_delay_seconds=normalized_retry_delay,
        )
        job.add_log(
            "Job queued",
            max_attempts=job.max_attempts,
            retry_delay_seconds=job.retry_delay_seconds,
        )
        await self.repository.add(job)
        await self._events.publish(job)
        logger.bind(
            job_id=job.id,
            job_type=job.job_type,
            project_id=project_id,
            max_attempts=job.max_attempts,
        ).info("Job enqueued")
        if self._queue is not None:
            await self._queue.enqueue(job.id)
        else:  # pragma: no cover - should not happen during normal startup
            logger.bind(job_id=job.id).warning(
                "Job queue is not yet running; job will be picked up when workers start",
            )
        return job

    async def list_jobs(self, project_id: str, statuses: Optional[set[str]] = None) -> list[Job]:
        return await self.repository.list_by_project(project_id, statuses=statuses)

    async def get_job(self, job_id: str) -> Optional[Job]:
        return await self.repository.get(job_id)

    async def delete_job(self, job_id: str) -> None:
        await self.repository.delete(job_id)

    async def append_log(self, job: Job, message: str, level: str = "INFO", **details: Any) -> Job:
        job.add_log(message, level=level, **details)
        await self.repository.update(job)
        await self._events.publish(job)
        logger.bind(job_id=job.id, **details).log(level.upper(), message)
        return job

    async def update_progress(
        self,
        job: Job,
        progress: Union[int, float],
        message: Optional[str] = None,
        level: str = "INFO",
        **details: Any,
    ) -> Job:
        job.progress = max(0.0, min(float(progress), 100.0))
        if message:
            job.add_log(message, level=level, **details)
        else:
            job.updated_at = datetime.utcnow()
        await self.repository.update(job)
        await self._events.publish(job)
        return job

    async def mark_running(self, job: Job) -> Job:
        job.status = JobStatus.RUNNING
        job.error_message = None
        job.progress = 0.0
        job.result = {}
        job.attempts += 1
        job.add_log(
            "Job started",
            attempt=job.attempts,
            max_attempts=job.max_attempts,
        )
        await self.repository.update(job)
        await self._events.publish(job)
        logger.bind(
            job_id=job.id,
            job_type=job.job_type,
            attempt=job.attempts,
            max_attempts=job.max_attempts,
        ).info("Job started")
        return job

    async def mark_completed(self, job: Job, result: Optional[JobResult] = None) -> Job:
        job.status = JobStatus.COMPLETED
        job.progress = 100.0
        job.error_message = None
        if result is not None:
            job.result = result
        job.add_log("Job completed successfully")
        await self.repository.update(job)
        await self._events.publish(job)
        logger.bind(job_id=job.id, job_type=job.job_type).info("Job completed")
        return job

    async def mark_failed(self, job: Job, error_message: str, exc: Optional[BaseException] = None) -> Job:
        job.status = JobStatus.FAILED
        job.error_message = error_message
        job.add_log(
            "Job failed",
            level="ERROR",
            error=error_message,
            attempt=job.attempts,
            max_attempts=job.max_attempts,
        )
        await self.repository.update(job)
        await self._events.publish(job)
        log = logger.bind(job_id=job.id, job_type=job.job_type, error=error_message, attempt=job.attempts)
        if exc is not None:
            log.exception("Job failed")
        else:
            log.error("Job failed")
        return job

    async def handle_job_failure(
        self,
        job: Job,
        error_message: str,
        *,
        exc: Optional[BaseException] = None,
    ) -> Job:
        if job.attempts < job.max_attempts:
            job.status = JobStatus.QUEUED
            job.error_message = error_message
            job.progress = 0.0
            job.add_log(
                "Job failed; retry scheduled",
                level="ERROR",
                error=error_message,
                attempt=job.attempts,
                max_attempts=job.max_attempts,
                retry_delay_seconds=job.retry_delay_seconds,
            )
            await self.repository.update(job)
            await self._events.publish(job)
            log = logger.bind(
                job_id=job.id,
                job_type=job.job_type,
                error=error_message,
                attempt=job.attempts,
                max_attempts=job.max_attempts,
                retry_delay=job.retry_delay_seconds,
            )
            if exc is not None:
                log.opt(exception=exc).warning("Job failed; queued for retry")
            else:
                log.warning("Job failed; queued for retry")
            if self._queue is not None:
                delay = job.retry_delay_seconds
                if delay > 0:
                    await self._queue.schedule_retry(job.id, delay)
                else:
                    await self._queue.enqueue(job.id)
            return job

        return await self.mark_failed(job, error_message, exc=exc)

    async def recover_incomplete_jobs(self) -> list[Job]:
        jobs = await self.repository.all_jobs()
        recovered: list[Job] = []
        for job in jobs:
            if job.status == JobStatus.QUEUED:
                recovered.append(job)
            elif job.status == JobStatus.RUNNING:
                job.status = JobStatus.QUEUED
                job.progress = 0.0
                job.result = {}
                job.add_log(
                    "Recovered unfinished job",
                    level="WARNING",
                    attempt=job.attempts,
                    max_attempts=job.max_attempts,
                )
                await self.repository.update(job)
                await self._events.publish(job)
                recovered.append(job)
        if recovered:
            logger.bind(count=len(recovered)).info("Recovered pending jobs")
        return recovered

    async def watch_job(self, job_id: str) -> AsyncIterator[dict[str, Any]]:
        queue = await self._events.subscribe(job_id)
        try:
            while True:
                payload = await queue.get()
                yield payload
        finally:
            await self._events.unsubscribe(job_id, queue)

    def serialize(self, job: Job) -> dict[str, Any]:
        return job.model_dump(mode="json")


@dataclass
class JobExecutionContext:
    """Runtime helper passed to job handlers."""

    service: JobService
    job: Job
    worker_id: Optional[int] = None

    @property
    def job_id(self) -> str:
        return self.job.id

    @property
    def payload(self) -> dict[str, Any]:
        return self.job.payload

    @property
    def project_id(self) -> str:
        return self.job.project_id

    async def log(self, message: str, level: str = "INFO", **details: Any) -> None:
        self.job = await self.service.append_log(self.job, message, level=level, **details)

    async def progress(self, value: Union[int, float], message: Optional[str] = None, level: str = "INFO", **details: Any) -> None:
        self.job = await self.service.update_progress(self.job, value, message=message, level=level, **details)

    async def mark_completed(self, result: Optional[dict[str, Any]] = None) -> None:
        self.job = await self.service.mark_completed(self.job, result=result)

    async def mark_failed(self, error_message: str, exc: Optional[BaseException] = None) -> None:
        self.job = await self.service.mark_failed(self.job, error_message, exc=exc)
