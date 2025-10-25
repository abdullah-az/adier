from __future__ import annotations

import json
from typing import AsyncIterator

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_job_service, get_timeline_service
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.timeline import (
    BackgroundMusicUpdateRequest,
    ExportTemplateUpdateRequest,
    SubtitleTrackUpsertRequest,
    TimelineCreateRequest,
    TimelineJobResponse,
    TimelineProgressPayload,
    TimelineResponse,
    TimelineSegmentPayload,
    TimelineSummary,
    TimelineThumbnailResponse,
    TimelineUpdateRequest,
    WatermarkUpdateRequest,
)
from app.services.job_service import JobService
from app.services.timeline_service import TimelineService, TimelineValidationError
from app.utils.responses import empty_response, error_response, paginated_response, success_response

router = APIRouter(prefix="/projects/{project_id}/timelines", tags=["timelines"])


def _format_sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


@router.get(
    "",
    response_model=PaginatedResponse[TimelineSummary],
    summary="List timelines for a project",
)
async def list_timelines(
    project_id: str,
    timeline_service: TimelineService = Depends(get_timeline_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
) -> PaginatedResponse[TimelineSummary]:
    timelines = await timeline_service.list_timelines(project_id)
    timelines.sort(key=lambda timeline: timeline.created_at)
    total = len(timelines)
    start = (page - 1) * page_size
    end = start + page_size
    sliced = timelines[start:end]
    items = [TimelineSummary.from_model(timeline) for timeline in sliced]
    return paginated_response(
        items,
        page=page,
        page_size=page_size,
        total_items=total,
        message="Timelines retrieved",
    )


@router.post(
    "",
    response_model=ApiResponse[TimelineResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a timeline",
)
async def create_timeline(
    project_id: str,
    payload: TimelineCreateRequest,
    timeline_service: TimelineService = Depends(get_timeline_service),
) -> ApiResponse[TimelineResponse]:
    try:
        timeline = await timeline_service.create_timeline(
            project_id,
            name=payload.name,
            description=payload.description,
            locale=payload.locale,
            segments=[segment.to_model() for segment in payload.segments],
            aspect_ratio=payload.aspect_ratio,
            resolution=payload.resolution,
            proxy_resolution=payload.proxy_resolution,
            generate_thumbnails=payload.generate_thumbnails,
            background_music=payload.background_music,
            export_templates=payload.export_templates,
            default_watermark=payload.default_watermark,
        )
    except TimelineValidationError as exc:
        return error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="TIMELINE_INVALID",
            message=str(exc),
        )
    return success_response(
        TimelineResponse.from_model(timeline),
        message="Timeline created",
        code="TIMELINE_CREATED",
    )



@router.get(
    "/{timeline_id}",
    response_model=ApiResponse[TimelineResponse],
    summary="Get timeline details",
)
async def get_timeline(
    project_id: str,
    timeline_id: str,
    timeline_service: TimelineService = Depends(get_timeline_service),
) -> ApiResponse[TimelineResponse]:
    timeline = await timeline_service.get_timeline(project_id, timeline_id)
    if timeline is None:
        return error_response(status_code=status.HTTP_404_NOT_FOUND, code="TIMELINE_NOT_FOUND", message="Timeline not found")
    return success_response(TimelineResponse.from_model(timeline), message="Timeline fetched")


@router.patch(
    "/{timeline_id}",
    response_model=ApiResponse[TimelineResponse],
    summary="Update timeline details",
)
async def update_timeline(
    project_id: str,
    timeline_id: str,
    payload: TimelineUpdateRequest,
    timeline_service: TimelineService = Depends(get_timeline_service),
) -> ApiResponse[TimelineResponse]:
    segments = None
    if payload.segments is not None:
        segments = [segment.to_model() for segment in payload.segments]
    try:
        timeline = await timeline_service.update_timeline(
            project_id,
            timeline_id,
            name=payload.name,
            description=payload.description,
            locale=payload.locale,
            segments=segments,
            aspect_ratio=payload.aspect_ratio,
            resolution=payload.resolution,
            proxy_resolution=payload.proxy_resolution,
            generate_thumbnails=payload.generate_thumbnails,
        )
    except TimelineValidationError as exc:
        return error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="TIMELINE_INVALID",
            message=str(exc),
        )
    if timeline is None:
        return error_response(status_code=status.HTTP_404_NOT_FOUND, code="TIMELINE_NOT_FOUND", message="Timeline not found")
    return success_response(TimelineResponse.from_model(timeline), message="Timeline updated")


@router.delete(
    "/{timeline_id}",
    response_model=ApiResponse[None],
    summary="Delete a timeline",
)
async def delete_timeline(
    project_id: str,
    timeline_id: str,
    timeline_service: TimelineService = Depends(get_timeline_service),
) -> ApiResponse[None]:
    deleted = await timeline_service.delete_timeline(project_id, timeline_id)
    if not deleted:
        return error_response(status_code=status.HTTP_404_NOT_FOUND, code="TIMELINE_NOT_FOUND", message="Timeline not found")
    return empty_response(message="Timeline deleted", code="TIMELINE_DELETED")


@router.put(
    "/{timeline_id}/music",
    response_model=ApiResponse[TimelineResponse],
    summary="Set background music for timeline",
)
async def set_background_music(
    project_id: str,
    timeline_id: str,
    payload: BackgroundMusicUpdateRequest,
    timeline_service: TimelineService = Depends(get_timeline_service),
) -> ApiResponse[TimelineResponse]:
    try:
        timeline = await timeline_service.set_background_music(project_id, timeline_id, payload.background_music)
    except TimelineValidationError as exc:
        return error_response(status_code=status.HTTP_400_BAD_REQUEST, code="TIMELINE_INVALID", message=str(exc))
    if timeline is None:
        return error_response(status_code=status.HTTP_404_NOT_FOUND, code="TIMELINE_NOT_FOUND", message="Timeline not found")
    return success_response(TimelineResponse.from_model(timeline), message="Background music updated")


@router.put(
    "/{timeline_id}/subtitles",
    response_model=ApiResponse[TimelineResponse],
    summary="Upsert a subtitle track",
)
async def upsert_subtitle_track(
    project_id: str,
    timeline_id: str,
    payload: SubtitleTrackUpsertRequest,
    timeline_service: TimelineService = Depends(get_timeline_service),
) -> ApiResponse[TimelineResponse]:
    try:
        timeline = await timeline_service.upsert_subtitle_track(project_id, timeline_id, payload.track.to_model())
    except TimelineValidationError as exc:
        return error_response(status_code=status.HTTP_400_BAD_REQUEST, code="SUBTITLE_INVALID", message=str(exc))
    if timeline is None:
        return error_response(status_code=status.HTTP_404_NOT_FOUND, code="TIMELINE_NOT_FOUND", message="Timeline not found")
    return success_response(TimelineResponse.from_model(timeline), message="Subtitle track saved")


@router.put(
    "/{timeline_id}/export-templates",
    response_model=ApiResponse[TimelineResponse],
    summary="Update export templates",
)
async def update_export_templates(
    project_id: str,
    timeline_id: str,
    payload: ExportTemplateUpdateRequest,
    timeline_service: TimelineService = Depends(get_timeline_service),
) -> ApiResponse[TimelineResponse]:
    timeline = await timeline_service.update_export_templates(project_id, timeline_id, payload.templates)
    if timeline is None:
        return error_response(status_code=status.HTTP_404_NOT_FOUND, code="TIMELINE_NOT_FOUND", message="Timeline not found")
    return success_response(TimelineResponse.from_model(timeline), message="Export templates updated")


@router.put(
    "/{timeline_id}/watermark",
    response_model=ApiResponse[TimelineResponse],
    summary="Set default watermark",
)
async def set_default_watermark(
    project_id: str,
    timeline_id: str,
    payload: WatermarkUpdateRequest,
    timeline_service: TimelineService = Depends(get_timeline_service),
) -> ApiResponse[TimelineResponse]:
    timeline = await timeline_service.set_default_watermark(project_id, timeline_id, payload.watermark)
    if timeline is None:
        return error_response(status_code=status.HTTP_404_NOT_FOUND, code="TIMELINE_NOT_FOUND", message="Timeline not found")
    return success_response(TimelineResponse.from_model(timeline), message="Watermark updated")


@router.post(
    "/{timeline_id}/preview",
    response_model=ApiResponse[TimelineJobResponse],
    summary="Trigger a preview rendering job",
)
async def create_preview(
    project_id: str,
    timeline_id: str,
    timeline_service: TimelineService = Depends(get_timeline_service),
) -> ApiResponse[TimelineJobResponse]:
    timeline = await timeline_service.get_timeline(project_id, timeline_id)
    if timeline is None:
        return error_response(status_code=status.HTTP_404_NOT_FOUND, code="TIMELINE_NOT_FOUND", message="Timeline not found")
    try:
        job_id = await timeline_service.create_preview_job(timeline)
    except TimelineValidationError as exc:
        return error_response(status_code=status.HTTP_400_BAD_REQUEST, code="TIMELINE_INVALID", message=str(exc))
    return success_response(TimelineJobResponse(job_id=job_id, operation="preview"), message="Preview job enqueued")


@router.post(
    "/{timeline_id}/export",
    response_model=ApiResponse[TimelineJobResponse],
    summary="Trigger an export job",
)
async def create_export(
    project_id: str,
    timeline_id: str,
    timeline_service: TimelineService = Depends(get_timeline_service),
) -> ApiResponse[TimelineJobResponse]:
    timeline = await timeline_service.get_timeline(project_id, timeline_id)
    if timeline is None:
        return error_response(status_code=status.HTTP_404_NOT_FOUND, code="TIMELINE_NOT_FOUND", message="Timeline not found")
    try:
        job_id = await timeline_service.create_export_job(timeline)
    except TimelineValidationError as exc:
        return error_response(status_code=status.HTTP_400_BAD_REQUEST, code="TIMELINE_INVALID", message=str(exc))
    return success_response(TimelineJobResponse(job_id=job_id, operation="export"), message="Export job enqueued")


@router.get(
    "/{timeline_id}/progress",
    response_model=ApiResponse[TimelineProgressPayload],
    summary="Get export and preview progress",
)
async def timeline_progress(
    project_id: str,
    timeline_id: str,
    timeline_service: TimelineService = Depends(get_timeline_service),
) -> ApiResponse[TimelineProgressPayload]:
    timeline = await timeline_service.get_timeline(project_id, timeline_id)
    if timeline is None:
        return error_response(status_code=status.HTTP_404_NOT_FOUND, code="TIMELINE_NOT_FOUND", message="Timeline not found")
    progress = await timeline_service.job_progress(project_id, timeline)
    return success_response(TimelineProgressPayload(**progress), message="Progress retrieved")


@router.get(
    "/{timeline_id}/thumbnails",
    response_model=ApiResponse[list[TimelineThumbnailResponse]],
    summary="List generated thumbnails for a timeline",
)
async def timeline_thumbnails(
    project_id: str,
    timeline_id: str,
    timeline_service: TimelineService = Depends(get_timeline_service),
) -> ApiResponse[list[TimelineThumbnailResponse]]:
    timeline = await timeline_service.get_timeline(project_id, timeline_id)
    if timeline is None:
        return error_response(status_code=status.HTTP_404_NOT_FOUND, code="TIMELINE_NOT_FOUND", message="Timeline not found")
    thumbnails = await timeline_service.collect_segment_thumbnails(timeline)
    payload = [TimelineThumbnailResponse(**thumbnail) for thumbnail in thumbnails]
    return success_response(payload, message="Thumbnails retrieved")


@router.get(
    "/{timeline_id}/jobs/{job_id}/events",
    summary="Stream job events for a timeline",
)
async def stream_timeline_events(
    project_id: str,
    timeline_id: str,
    job_id: str,
    timeline_service: TimelineService = Depends(get_timeline_service),
    job_service: JobService = Depends(get_job_service),
) -> StreamingResponse:
    timeline = await timeline_service.get_timeline(project_id, timeline_id)
    if timeline is None:
        return error_response(status_code=status.HTTP_404_NOT_FOUND, code="TIMELINE_NOT_FOUND", message="Timeline not found")
    job = await job_service.get_job(job_id)
    if job is None or job.project_id != project_id:
        return error_response(status_code=status.HTTP_404_NOT_FOUND, code="JOB_NOT_FOUND", message="Job not found")
    if job.payload.get("timeline_id") != timeline_id:
        return error_response(status_code=status.HTTP_400_BAD_REQUEST, code="JOB_MISMATCH", message="Job not associated with timeline")

    async def event_generator() -> AsyncIterator[str]:
        yield _format_sse(job_service.serialize(job))
        async for update in job_service.watch_job(job_id):
            yield _format_sse(update)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
