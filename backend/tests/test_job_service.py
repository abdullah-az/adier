from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

import pytest

from app.models.job import JobStatus
from app.repositories.job_repository import JobRepository
from app.services.job_service import JobService


@dataclass
class CapturingQueue:
    enqueued: list[str]

    def __init__(self) -> None:
        self.enqueued = []

    async def enqueue(self, job_id: str) -> None:
        self.enqueued.append(job_id)

    async def schedule_retry(self, job_id: str, delay: float) -> None:
        self.enqueued.append(job_id)


@pytest.fixture
def job_service(temp_storage_dir: Path) -> tuple[JobService, CapturingQueue]:
    repository = JobRepository(temp_storage_dir)
    service = JobService(repository, default_max_attempts=2, default_retry_delay=0.0)
    queue = CapturingQueue()
    service.attach_queue(queue)
    return service, queue


@pytest.mark.asyncio
async def test_create_job_persists_and_enqueues(job_service: tuple[JobService, CapturingQueue]):
    service, queue = job_service
    job = await service.create_job("project-1", "ingest", payload={"asset_id": "asset-123"})

    assert job.id in queue.enqueued
    stored = await service.get_job(job.id)
    assert stored is not None
    assert stored.status == JobStatus.QUEUED
    assert stored.payload["asset_id"] == "asset-123"
    assert stored.logs, "expected initial log entry to be recorded"


@pytest.mark.asyncio
async def test_job_progress_and_completion(job_service: tuple[JobService, CapturingQueue]):
    service, _ = job_service
    job = await service.create_job("project-2", "scene_detection")

    job = await service.mark_running(job)
    job = await service.update_progress(job, 45.0, message="half way")
    assert job.progress == 45.0
    assert job.logs[-1].message == "half way"

    await service.mark_completed(job, result={"summary": "done"})
    stored = await service.get_job(job.id)
    assert stored is not None
    assert stored.status == JobStatus.COMPLETED
    assert stored.result == {"summary": "done"}


@pytest.mark.asyncio
async def test_handle_job_failure_retries_then_fails(job_service: tuple[JobService, CapturingQueue]):
    service, queue = job_service
    job = await service.create_job("project-3", "transcription", max_attempts=2)

    job = await service.mark_running(job)
    await service.handle_job_failure(job, "first attempt failed")

    assert queue.enqueued[-1] == job.id
    queued_job = await service.get_job(job.id)
    assert queued_job is not None
    assert queued_job.status == JobStatus.QUEUED
    assert queued_job.error_message == "first attempt failed"

    queued_job = await service.mark_running(queued_job)
    await service.handle_job_failure(queued_job, "second failure")

    final = await service.get_job(job.id)
    assert final is not None
    assert final.status == JobStatus.FAILED
    assert final.error_message == "second failure"
    assert final.attempts == 2


@pytest.mark.asyncio
async def test_watch_job_streams_updates(job_service: tuple[JobService, CapturingQueue]):
    service, _ = job_service
    job = await service.create_job("project-4", "ingest")

    events: list[dict] = []

    async def _consume_updates() -> None:
        async for payload in service.watch_job(job.id):
            events.append(payload)
            if len(events) >= 2:
                break

    consumer = asyncio.create_task(_consume_updates())
    await asyncio.sleep(0)

    running = await service.mark_running(job)
    await asyncio.sleep(0)
    await service.mark_completed(running)

    await asyncio.wait_for(consumer, timeout=1.0)

    assert events
    assert events[0]["status"] == JobStatus.RUNNING
    assert events[-1]["status"] == JobStatus.COMPLETED
