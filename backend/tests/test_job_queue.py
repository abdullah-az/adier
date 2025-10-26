from __future__ import annotations

from pathlib import Path

import pytest

from app.models.job import JobStatus
from app.repositories.job_repository import JobRepository
from app.services.job_service import JobExecutionContext, JobService
from app.workers.job_queue import JobQueue, drain_queue


@pytest.mark.asyncio
async def test_job_queue_processes_job_successfully(temp_storage_dir: Path):
    repository = JobRepository(temp_storage_dir)
    service = JobService(repository, default_max_attempts=2, default_retry_delay=0.0)
    queue = JobQueue(service, concurrency=1, maxsize=10)

    async def handler(context: JobExecutionContext):
        await context.log("Processing job")
        return {"status": "ok"}

    service.register_handler("demo", handler)

    await queue.start()
    try:
        job = await service.create_job("project", "demo")
        await drain_queue(queue, timeout=1.0)
        stored = await service.get_job(job.id)
        assert stored is not None
        assert stored.status == JobStatus.COMPLETED
        assert stored.result == {"status": "ok"}
    finally:
        await queue.stop()


@pytest.mark.asyncio
async def test_job_queue_retries_until_success(temp_storage_dir: Path):
    repository = JobRepository(temp_storage_dir)
    service = JobService(repository, default_max_attempts=3, default_retry_delay=0.0)
    queue = JobQueue(service, concurrency=1, maxsize=10)

    attempts = 0

    async def flaky_handler(context: JobExecutionContext):
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise RuntimeError("transient failure")
        return {"attempts": attempts}

    service.register_handler("flaky", flaky_handler)

    await queue.start()
    try:
        job = await service.create_job("project", "flaky", max_attempts=3)
        await drain_queue(queue, timeout=1.0)
        stored = await service.get_job(job.id)
        assert stored is not None
        assert stored.status == JobStatus.COMPLETED
        assert stored.attempts == 2
        assert stored.result == {"attempts": 2}
    finally:
        await queue.stop()


@pytest.mark.asyncio
async def test_job_queue_marks_failed_after_exhausting_attempts(temp_storage_dir: Path):
    repository = JobRepository(temp_storage_dir)
    service = JobService(repository, default_max_attempts=2, default_retry_delay=0.0)
    queue = JobQueue(service, concurrency=1, maxsize=10)

    async def failing_handler(context: JobExecutionContext):
        await context.log("About to fail", level="ERROR")
        raise RuntimeError("permanent failure")

    service.register_handler("always_fail", failing_handler)

    await queue.start()
    try:
        job = await service.create_job("project", "always_fail", max_attempts=2)
        await drain_queue(queue, timeout=1.0)
        stored = await service.get_job(job.id)
        assert stored is not None
        assert stored.status == JobStatus.FAILED
        assert stored.attempts == 2
        assert stored.error_message == "permanent failure"
    finally:
        await queue.stop()
