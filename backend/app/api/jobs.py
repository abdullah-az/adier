from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_job_service
from app.models.job import JobStatus
from app.schemas.job import JobCreateRequest, JobResponse
from app.services.job_service import JobService

router = APIRouter(prefix="/projects/{project_id}", tags=["jobs"])


def _format_sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def submit_job(
    project_id: str,
    request: JobCreateRequest,
    job_service: JobService = Depends(get_job_service),
) -> JobResponse:
    job = await job_service.create_job(project_id, request.job_type, payload=request.payload)
    return JobResponse.from_model(job)


@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs(
    project_id: str,
    status_filter: Optional[list[str]] = Query(None, alias="status", description="Filter by job status"),
    job_service: JobService = Depends(get_job_service),
) -> list[JobResponse]:
    statuses: Optional[set[str]] = None
    if status_filter:
        statuses = {status.lower() for status in status_filter}
        valid_statuses = {status.value for status in JobStatus}
        invalid = statuses - valid_statuses
        if invalid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter(s): {', '.join(sorted(invalid))}",
            )
    jobs = await job_service.list_jobs(project_id, statuses=statuses)
    return [JobResponse.from_model(job) for job in jobs]


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def job_detail(
    project_id: str,
    job_id: str,
    job_service: JobService = Depends(get_job_service),
) -> JobResponse:
    job = await job_service.get_job(job_id)
    if job is None or job.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobResponse.from_model(job)


@router.get("/jobs/{job_id}/events")
async def stream_job_events(
    project_id: str,
    job_id: str,
    job_service: JobService = Depends(get_job_service),
) -> StreamingResponse:
    job = await job_service.get_job(job_id)
    if job is None or job.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    async def event_generator() -> AsyncIterator[str]:
        try:
            yield _format_sse(job_service.serialize(job))
            async for update in job_service.watch_job(job_id):
                yield _format_sse(update)
        except asyncio.CancelledError:  # pragma: no cover - connection closed
            raise

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
