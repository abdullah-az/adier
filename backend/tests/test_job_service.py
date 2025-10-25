from __future__ import annotations

import asyncio

import pytest

from app.models.job import JobStatus
from app.repositories.job_repository import JobRepository
from app.services.job_service import JobService


@pytest.mark.asyncio
async def test_job_service_event_stream(tmp_path):
    repository = JobRepository(storage_root=tmp_path)
    service = JobService(repository)

    job = await service.create_job("demo", "ingest", payload={"asset_id": "asset-123"})

    events: list[dict] = []

    async def collect_events():
        async for payload in service.watch_job(job.id):
            events.append(payload)
            if len(events) >= 2:
                break

    collector = asyncio.create_task(collect_events())

    await service.mark_running(job)
    await service.mark_completed(job, result={"ok": True})

    await collector

    assert events
    statuses = [event["status"] for event in events]
    assert JobStatus.RUNNING in statuses
    assert JobStatus.COMPLETED in statuses
    assert events[-1]["result"] == {"ok": True}


@pytest.mark.asyncio
async def test_job_service_recovery(tmp_path):
    repository = JobRepository(storage_root=tmp_path)
    service = JobService(repository)

    running_job = await service.create_job("demo", "transcription")
    running_job.status = JobStatus.RUNNING
    await repository.update(running_job)

    queued_job = await service.create_job("demo", "scene_detection")
    queued_job.status = JobStatus.QUEUED
    await repository.update(queued_job)

    recovered = await service.recover_incomplete_jobs()
    assert len(recovered) == 2
    recovered_map = {job.id: job for job in recovered}
    assert recovered_map[running_job.id].status == JobStatus.QUEUED
    assert recovered_map[queued_job.id].status == JobStatus.QUEUED
