from __future__ import annotations

import pytest

from app.models.job import JobStatus
from app.models.pipeline import GeneratedMedia, TimelineClip, TimelineCompositionRequest, TimelineCompositionResult
from app.repositories.job_repository import JobRepository
from app.services.job_service import JobExecutionContext, JobService
from app.services.video_pipeline_service import PipelineError
from app.workers.handlers import (
    create_export_handler,
    ingest_handler,
    scene_detection_handler,
    transcription_handler,
)


class NoopQueue:
    async def enqueue(self, job_id: str) -> None:  # pragma: no cover - helper
        return None

    async def schedule_retry(self, job_id: str, delay: float) -> None:  # pragma: no cover - helper
        return None


@pytest.fixture
def job_service(temp_storage_dir):
    repository = JobRepository(temp_storage_dir)
    service = JobService(repository, default_max_attempts=2, default_retry_delay=0.0)
    service.attach_queue(NoopQueue())
    return service


async def _build_context(service: JobService, job_type: str, payload: dict | None = None) -> JobExecutionContext:
    job = await service.create_job("project", job_type, payload=payload)
    job = await service.mark_running(job)
    return JobExecutionContext(service=service, job=job, worker_id=1)


@pytest.mark.asyncio
async def test_ingest_handler_records_result(job_service: JobService):
    context = await _build_context(job_service, "ingest", payload={"asset_id": "asset-42"})

    result = await ingest_handler(context)

    assert result["asset_id"] == "asset-42"
    stored = await job_service.get_job(context.job.id)
    assert stored is not None
    assert stored.logs, "expected logs to be appended during handler execution"


@pytest.mark.asyncio
async def test_scene_detection_handler_returns_scenes(job_service: JobService):
    context = await _build_context(job_service, "scene_detection")

    result = await scene_detection_handler(context)

    assert "scenes" in result
    assert len(result["scenes"]) == 3
    stored = await job_service.get_job(context.job.id)
    assert stored is not None
    assert any("Scene detection" in entry.message for entry in stored.logs)


@pytest.mark.asyncio
async def test_transcription_handler_returns_placeholder(job_service: JobService):
    context = await _build_context(job_service, "transcription", payload={"language": "es"})

    result = await transcription_handler(context)

    assert result["language"] == "es"
    assert "placeholder transcript" in result["transcript"]


class StubPipelineService:
    def __init__(self) -> None:
        self.invocations: list[tuple[str, TimelineCompositionRequest]] = []

    async def compose_timeline(self, project_id: str, request: TimelineCompositionRequest, **_: object) -> TimelineCompositionResult:
        self.invocations.append((project_id, request))
        return TimelineCompositionResult(
            timeline=GeneratedMedia(path="processed/timeline.mp4", category="processed", metadata={}),
            proxy=None,
            exports=[GeneratedMedia(path="export/final.mp4", category="export", metadata={})],
            thumbnails=[],
        )


@pytest.mark.asyncio
async def test_export_handler_invokes_pipeline(job_service: JobService):
    pipeline = StubPipelineService()
    handler = create_export_handler(pipeline)
    request = TimelineCompositionRequest(clips=[TimelineClip(asset_id="asset-99", in_point=0, out_point=5)])
    context = await _build_context(job_service, "export", payload={"timeline": request.model_dump(mode="json")})

    result = await handler(context)

    assert pipeline.invocations
    assert result["exports"]
    stored = await job_service.get_job(context.job.id)
    assert stored is not None
    assert stored.logs[-1].message == "Export pipeline complete"


class FailingPipelineService:
    async def compose_timeline(self, project_id: str, request: TimelineCompositionRequest, **_: object) -> TimelineCompositionResult:
        raise PipelineError("invalid timeline")


@pytest.mark.asyncio
async def test_export_handler_raises_pipeline_errors(job_service: JobService):
    pipeline = FailingPipelineService()
    handler = create_export_handler(pipeline)
    request = TimelineCompositionRequest(clips=[TimelineClip(asset_id="asset", in_point=0, out_point=1)])
    context = await _build_context(job_service, "export", payload={"timeline": request.model_dump(mode="json")})

    with pytest.raises(PipelineError):
        await handler(context)

    stored = await job_service.get_job(context.job.id)
    assert stored is not None
    assert stored.status == JobStatus.RUNNING  # Handler raises before queue marks failure
    assert any(entry.level == "ERROR" for entry in stored.logs)
