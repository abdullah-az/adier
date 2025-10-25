from __future__ import annotations

import uuid

import pytest

from app.models.job import Job, JobStatus
from app.repositories.job_repository import JobRepository


@pytest.mark.asyncio
async def test_job_repository_crud(tmp_path):
    repository = JobRepository(storage_root=tmp_path)

    job = Job(
        id=str(uuid.uuid4()),
        project_id="demo",
        job_type="ingest",
        status=JobStatus.QUEUED,
        payload={"asset_id": "asset-1"},
    )

    await repository.add(job)

    stored = await repository.get(job.id)
    assert stored is not None
    assert stored.project_id == "demo"
    assert stored.status == JobStatus.QUEUED

    job.status = JobStatus.RUNNING
    job.progress = 42.0
    await repository.update(job)

    refreshed = await repository.get(job.id)
    assert refreshed is not None
    assert refreshed.status == JobStatus.RUNNING
    assert refreshed.progress == 42.0

    queued = await repository.list_by_project("demo", statuses={JobStatus.QUEUED.value})
    assert queued == []

    running = await repository.list_by_project("demo", statuses={JobStatus.RUNNING.value})
    assert len(running) == 1
    assert running[0].id == job.id

    await repository.delete(job.id)
    assert await repository.get(job.id) is None


@pytest.mark.asyncio
async def test_job_repository_filters_multiple_projects(tmp_path):
    repository = JobRepository(storage_root=tmp_path)

    demo_job = Job(id=str(uuid.uuid4()), project_id="demo", job_type="scene_detection")
    other_job = Job(id=str(uuid.uuid4()), project_id="other", job_type="export")

    await repository.add(demo_job)
    await repository.add(other_job)

    demo_jobs = await repository.list_by_project("demo")
    assert len(demo_jobs) == 1
    assert demo_jobs[0].id == demo_job.id

    all_jobs = await repository.all_jobs()
    assert {job.id for job in all_jobs} == {demo_job.id, other_job.id}
