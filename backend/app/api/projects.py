from __future__ import annotations

import math
from typing import Iterable, Optional

from fastapi import APIRouter, Body, Depends, Path, Query, status
from fastapi.responses import FileResponse

from app.api.dependencies import (
    get_ai_suggestion_service,
    get_job_service,
    get_project_service,
)
from app.api.errors import APIError
from app.models.pipeline import SubtitleSpec
from app.models.project import ClipTiming, Project, TimelineState
from app.schemas.ai import AISceneSuggestion, AISuggestionRequest, AISuggestionResponse
from app.schemas.common import AsyncOperationResponse, PaginationMeta
from app.schemas.media import MusicOption, MusicOptionsResponse, MusicSelectionRequest, ThumbnailResponse
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectResponse,
    ProjectSummary,
    ProjectUpdateRequest,
)
from app.schemas.timeline import TimelineLayoutItemRequest, TimelineResponse, TimelineUpdateRequest
from app.services.ai_service import AISuggestionService
from app.services.job_service import JobService
from app.services.project_service import ProjectNotFoundError, ProjectService, TimelineValidationError

router = APIRouter(prefix="/projects", tags=["projects"])


def _project_to_response(project: Project) -> ProjectResponse:
    return ProjectResponse.model_validate(project.model_dump())


def _project_to_summary(project: Project) -> ProjectSummary:
    thumbnail = None
    timeline: Optional[TimelineState] = project.timeline
    if timeline and timeline.layout:
        first_clip = timeline.layout[0]
        thumbnail = timeline.metadata.get("hero_thumbnail") if timeline.metadata else None
        if thumbnail is None:
            clip_metadata = first_clip.metadata or {}
            thumbnail = clip_metadata.get("thumbnail")
    return ProjectSummary(
        id=project.id,
        name=project.name,
        status=project.status,
        updated_at=project.updated_at,
        primary_locale=project.primary_locale,
        thumbnail_url=thumbnail,
    )


def _timeline_to_response(timeline: TimelineState) -> TimelineResponse:
    return TimelineResponse(timeline=timeline, layout=timeline.layout, total_duration=timeline.total_duration)


def _build_layout_models(layout: Iterable[TimelineLayoutItemRequest]) -> list[ClipTiming]:
    return [
        ClipTiming(
            clip_id=item.clip_id,
            asset_id=item.asset_id,
            start=item.start,
            duration=item.duration,
            in_point=item.in_point,
            out_point=item.out_point,
            include_audio=item.include_audio,
            label=item.label,
            metadata=item.metadata or {},
        )
        for item in layout
    ]


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort: str = Query("created_at:desc", description="Sort expression e.g. created_at:desc"),
    locale: Optional[str] = Query(None, description="Filter projects that support the specified locale"),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectListResponse:
    projects, total = await project_service.list_projects(page=page, page_size=page_size, sort=sort, locale=locale)
    summaries = [_project_to_summary(project) for project in projects]
    total_pages = math.ceil(total / page_size) if total else 0
    meta = PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        sort=sort,
        locale=locale,
    )
    return ProjectListResponse(items=summaries, pagination=meta)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreateRequest,
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    project = await project_service.create_project(
        name=payload.name,
        description=payload.description,
        primary_locale=payload.primary_locale,
        supported_locales=payload.supported_locales,
        tags=payload.tags,
        metadata=payload.metadata,
        project_id=payload.project_id,
    )
    return _project_to_response(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str = Path(..., description="Project identifier"),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    try:
        project = await project_service.get_project(project_id)
    except ProjectNotFoundError as exc:
        raise APIError(status_code=404, code="project_not_found", message="Project not found") from exc
    return _project_to_response(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    payload: ProjectUpdateRequest,
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    try:
        project = await project_service.update_project(
            project_id,
            name=payload.name,
            description=payload.description,
            status=payload.status,
            primary_locale=payload.primary_locale,
            supported_locales=payload.supported_locales,
            tags=payload.tags,
            metadata=payload.metadata,
        )
    except ProjectNotFoundError as exc:
        raise APIError(status_code=404, code="project_not_found", message="Project not found") from exc
    return _project_to_response(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    delete_storage: bool = Query(True, description="Whether to remove project files from storage"),
    project_service: ProjectService = Depends(get_project_service),
) -> None:
    try:
        await project_service.delete_project(project_id, delete_storage=delete_storage)
    except ProjectNotFoundError as exc:
        raise APIError(status_code=404, code="project_not_found", message="Project not found") from exc


@router.get("/{project_id}/timeline", response_model=TimelineResponse, tags=["timeline"])
async def get_timeline(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service),
) -> TimelineResponse:
    timeline = await project_service.get_timeline(project_id)
    if timeline is None:
        raise APIError(status_code=404, code="timeline_not_found", message="Timeline has not been created yet")
    return _timeline_to_response(timeline)


@router.put("/{project_id}/timeline", response_model=TimelineResponse, tags=["timeline"])
async def upsert_timeline(
    project_id: str,
    payload: TimelineUpdateRequest,
    project_service: ProjectService = Depends(get_project_service),
) -> TimelineResponse:
    layout_models = _build_layout_models(payload.layout)
    try:
        timeline = await project_service.update_timeline(
            project_id,
            composition=payload.composition,
            layout=layout_models,
            locale=payload.locale,
            metadata=payload.metadata,
            global_subtitles=payload.global_subtitles,
            background_music=payload.background_music,
        )
    except ProjectNotFoundError as exc:
        raise APIError(status_code=404, code="project_not_found", message="Project not found") from exc
    except TimelineValidationError as exc:
        raise APIError(status_code=422, code=exc.code, message=exc.message, details=exc.details) from exc
    return _timeline_to_response(timeline)


@router.patch("/{project_id}/timeline/subtitles", response_model=TimelineResponse, tags=["timeline"])
async def update_timeline_subtitles(
    project_id: str,
    subtitles: Optional[SubtitleSpec] = Body(default=None),
    project_service: ProjectService = Depends(get_project_service),
) -> TimelineResponse:
    try:
        timeline = await project_service.update_timeline_subtitles(project_id, subtitles)
    except ProjectNotFoundError as exc:
        raise APIError(status_code=404, code="project_not_found", message="Project not found") from exc
    except TimelineValidationError as exc:
        raise APIError(status_code=409, code=exc.code, message=exc.message, details=exc.details) from exc
    return _timeline_to_response(timeline)


@router.put("/{project_id}/music/selection", response_model=TimelineResponse, tags=["music"])
async def update_music_selection(
    project_id: str,
    payload: MusicSelectionRequest,
    project_service: ProjectService = Depends(get_project_service),
) -> TimelineResponse:
    try:
        timeline = await project_service.update_timeline_music(project_id, payload.background_music)
    except ProjectNotFoundError as exc:
        raise APIError(status_code=404, code="project_not_found", message="Project not found") from exc
    except TimelineValidationError as exc:
        raise APIError(status_code=409, code=exc.code, message=exc.message, details=exc.details) from exc
    return _timeline_to_response(timeline)


@router.get("/{project_id}/music/options", response_model=MusicOptionsResponse, tags=["music"])
async def list_music_options(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service),
) -> MusicOptionsResponse:
    try:
        options = await project_service.list_music_options(project_id)
    except ProjectNotFoundError as exc:
        raise APIError(status_code=404, code="project_not_found", message="Project not found") from exc
    items = [MusicOption(**option) for option in options]
    return MusicOptionsResponse(items=items)


@router.post("/{project_id}/ai/suggestions", response_model=AISuggestionResponse, tags=["ai"])
async def generate_ai_suggestions(
    project_id: str,
    payload: AISuggestionRequest,
    ai_service: AISuggestionService = Depends(get_ai_suggestion_service),
) -> AISuggestionResponse:
    result = await ai_service.generate_scene_suggestions(
        project_id,
        locale=payload.locale,
        limit=payload.limit,
    )
    scenes = [AISceneSuggestion(**scene) for scene in result.get("scenes", [])]
    return AISuggestionResponse(
        locale=result.get("locale", payload.locale),
        generated_at=result.get("generated_at"),
        scenes=scenes,
        source_assets=result.get("source_assets", []),
    )


@router.post("/{project_id}/timeline/preview", response_model=AsyncOperationResponse, status_code=status.HTTP_202_ACCEPTED, tags=["timeline"])
async def trigger_preview_job(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service),
    job_service: JobService = Depends(get_job_service),
) -> AsyncOperationResponse:
    timeline = await project_service.get_timeline(project_id)
    if timeline is None:
        raise APIError(status_code=404, code="timeline_not_found", message="Timeline must be created before generating a preview")
    composition = timeline.composition.model_dump()
    job_payload = {
        "timeline": composition,
        "mode": "preview",
        "timeline_id": timeline.timeline_id,
        "layout": [clip.model_dump() for clip in timeline.layout],
        "total_duration": timeline.total_duration,
    }
    job = await job_service.create_job(project_id, "export", payload=job_payload)
    await project_service.record_timeline_job(project_id, job_id=job.id, kind="preview")
    return AsyncOperationResponse(
        job_id=job.id,
        status=job.status.value,
        message="Preview job enqueued",
        metadata={"operation": "preview"},
    )


@router.post("/{project_id}/exports", response_model=AsyncOperationResponse, status_code=status.HTTP_202_ACCEPTED, tags=["exports"])
async def trigger_export_job(
    project_id: str,
    include_preview_assets: bool = Query(False, description="Include preview proxies in export payload"),
    project_service: ProjectService = Depends(get_project_service),
    job_service: JobService = Depends(get_job_service),
) -> AsyncOperationResponse:
    timeline = await project_service.get_timeline(project_id)
    if timeline is None:
        raise APIError(status_code=404, code="timeline_not_found", message="Timeline must be created before requesting an export")
    composition = timeline.composition.model_dump()
    composition["include_preview_assets"] = include_preview_assets
    job_payload = {
        "timeline": composition,
        "mode": "export",
        "timeline_id": timeline.timeline_id,
        "layout": [clip.model_dump() for clip in timeline.layout],
        "total_duration": timeline.total_duration,
    }
    job = await job_service.create_job(project_id, "export", payload=job_payload)
    await project_service.record_timeline_job(project_id, job_id=job.id, kind="export")
    return AsyncOperationResponse(
        job_id=job.id,
        status=job.status.value,
        message="Export job enqueued",
        metadata={"operation": "export"},
    )


@router.get("/{project_id}/thumbnails", response_model=list[ThumbnailResponse], tags=["media"])
async def list_project_thumbnails(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service),
) -> list[ThumbnailResponse]:
    try:
        thumbnails = await project_service.list_thumbnails(project_id)
    except ProjectNotFoundError as exc:
        raise APIError(status_code=404, code="project_not_found", message="Project not found") from exc
    return [ThumbnailResponse(**thumb) for thumb in thumbnails]


@router.get("/{project_id}/files/{asset_id}", response_class=FileResponse, tags=["media"])
async def download_project_asset(
    project_id: str,
    asset_id: str,
    project_service: ProjectService = Depends(get_project_service),
) -> FileResponse:
    try:
        path, asset = await project_service.resolve_asset_path(asset_id, project_id=project_id)
    except (ProjectNotFoundError, FileNotFoundError) as exc:
        raise APIError(status_code=404, code="asset_not_found", message="Asset not found") from exc
    if not path.exists():
        raise APIError(status_code=404, code="asset_file_missing", message="Asset file is missing from storage")
    return FileResponse(
        path,
        media_type=asset.mime_type or "application/octet-stream",
        filename=asset.original_filename or path.name,
    )
