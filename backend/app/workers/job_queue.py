from __future__ import annotations

import asyncio
from typing import Optional

from loguru import logger

from app.models.job import JobStatus
from app.services.job_service import JobExecutionContext, JobService


class JobQueue:
    """Simple asyncio-backed job queue with worker coroutines."""

    def __init__(
        self,
        job_service: JobService,
        *,
        concurrency: int = 1,
        maxsize: int = 0,
    ) -> None:
        self.job_service = job_service
        self.concurrency = max(1, concurrency)
        queue_size = maxsize if maxsize > 0 else 0
        self._queue: asyncio.Queue[Optional[str]] = asyncio.Queue(maxsize=queue_size)
        self._workers: list[asyncio.Task[None]] = []
        self._started = False
        job_service.attach_queue(self)

    async def start(self) -> None:
        if self._started:
            return

        self._started = True
        pending = await self.job_service.recover_incomplete_jobs()
        for job in pending:
            await self.enqueue(job.id)

        for worker_id in range(self.concurrency):
            task = asyncio.create_task(self._worker_loop(worker_id), name=f"job-worker-{worker_id}")
            self._workers.append(task)

        logger.bind(workers=self.concurrency, recovered=len(pending)).info("Job queue started")

    async def stop(self) -> None:
        if not self._started:
            return

        self._started = False
        await self._queue.join()

        for _ in self._workers:
            await self._queue.put(None)

        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        logger.info("Job queue stopped")

    async def enqueue(self, job_id: str) -> None:
        await self._queue.put(job_id)
        logger.bind(job_id=job_id, pending=self._queue.qsize()).debug("Job queued for processing")

    async def _worker_loop(self, worker_id: int) -> None:
        logger.bind(worker_id=worker_id).debug("Worker started")
        try:
            while True:
                job_id = await self._queue.get()
                try:
                    if job_id is None:
                        break
                    await self._execute_job(job_id, worker_id)
                except asyncio.CancelledError:  # pragma: no cover - cooperative cancellation
                    raise
                except Exception as exc:  # pragma: no cover - defensive
                    logger.bind(worker_id=worker_id, job_id=job_id, error=str(exc)).exception(
                        "Worker encountered unexpected error",
                    )
                finally:
                    self._queue.task_done()
        finally:
            logger.bind(worker_id=worker_id).debug("Worker stopped")

    async def _execute_job(self, job_id: str, worker_id: int) -> None:
        job = await self.job_service.get_job(job_id)
        if job is None:
            logger.bind(job_id=job_id).warning("Received job that no longer exists")
            return

        handler = self.job_service.get_handler(job.job_type)
        if handler is None:
            await self.job_service.mark_failed(job, f"No handler registered for job type '{job.job_type}'")
            return

        job = await self.job_service.mark_running(job)
        context = JobExecutionContext(service=self.job_service, job=job, worker_id=worker_id)

        try:
            result = await handler(context)
        except asyncio.CancelledError:
            logger.bind(job_id=job_id, worker_id=worker_id).warning("Job execution cancelled")
            raise
        except Exception as exc:
            error_message = str(exc)
            await self.job_service.mark_failed(context.job, error_message, exc=exc)
            return

        if context.job.status == JobStatus.FAILED:
            return

        if context.job.status == JobStatus.RUNNING:
            final_result = result if result is not None else (context.job.result or None)
            await self.job_service.mark_completed(context.job, result=final_result)


async def drain_queue(queue: JobQueue, timeout: float = 5.0) -> None:
    """Utility to allow tests to wait for the queue to finish processing."""

    try:
        await asyncio.wait_for(queue._queue.join(), timeout=timeout)
    except asyncio.TimeoutError:  # pragma: no cover - defensive helper
        logger.warning("Timed out waiting for queue to drain")
