from __future__ import annotations

import pytest

from app.models.job import JobStatus
from app.repositories.job_repository import JobRepository
from app.services.job_service import JobService
from app.workers.job_queue import JobQueue, drain_queue


@pytest.mark.asyncio
async def test_job_queue_executes_registered_handler(tmp_path):
    repository = JobRepository(storage_root=tmp_path)
    service = JobService(repository)

    processed: list[str] = []

    async def handler(context):
        await context.log("handler-started")
        await context.progress(50.0, message="halfway")
        processed.append(context.job_id)
        return {"status": "ok"}

    service.register_handler("stub", handler)

    queue = JobQueue(service, concurrency=1)
    await queue.start()

    job = await service.create_job("demo", "stub")

    await drain_queue(queue, timeout=2.0)

    stored = await service.get_job(job.id)
    assert stored is not None
    assert stored.status == JobStatus.COMPLETED
    assert stored.result == {"status": "ok"}
    assert stored.progress == 100.0
    assert processed == [job.id]

    await queue.stop()
