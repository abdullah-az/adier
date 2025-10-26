from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_timeline_service
from app.schemas.timeline import (
    MusicSettingsPayload,
    MusicSettingsResponse,
    MusicTrackListResponse,
    MusicTrackResponse,
    SubtitleListResponse,
    SubtitleSegmentPayload,
    SubtitleUpdateRequest,
    TimelineSettingsResponse,
)
from app.services.timeline_service import TimelineSettingsService

router = APIRouter(prefix="/projects/{project_id}/timeline", tags=["timeline"])


def _serialize_subtitles(service_response) -> list[SubtitleSegmentPayload]:
    return [
        SubtitleSegmentPayload.model_validate(segment.model_dump())
        for segment in service_response
    ]


def _serialize_music_settings(service_response) -> MusicSettingsPayload:
    return MusicSettingsPayload.model_validate(service_response.model_dump())


@router.get("", response_model=TimelineSettingsResponse)
async def timeline_settings(
    project_id: str,
    timeline_service: TimelineSettingsService = Depends(get_timeline_service),
) -> TimelineSettingsResponse:
    settings = await timeline_service.get_settings(project_id)
    return TimelineSettingsResponse(
        subtitles=_serialize_subtitles(settings.subtitles),
        music=_serialize_music_settings(settings.music),
        updated_at=settings.updated_at,
    )


@router.get("/subtitles", response_model=SubtitleListResponse)
async def list_subtitles(
    project_id: str,
    timeline_service: TimelineSettingsService = Depends(get_timeline_service),
) -> SubtitleListResponse:
    settings = await timeline_service.get_settings(project_id)
    return SubtitleListResponse(
        segments=_serialize_subtitles(settings.subtitles),
        updated_at=settings.updated_at,
    )


@router.put("/subtitles", response_model=SubtitleListResponse, status_code=status.HTTP_200_OK)
async def update_subtitles(
    project_id: str,
    request: SubtitleUpdateRequest,
    timeline_service: TimelineSettingsService = Depends(get_timeline_service),
) -> SubtitleListResponse:
    settings = await timeline_service.update_subtitles(project_id, request.segments)
    return SubtitleListResponse(
        segments=_serialize_subtitles(settings.subtitles),
        updated_at=settings.updated_at,
    )


@router.get("/music/tracks", response_model=MusicTrackListResponse)
async def list_music_tracks(
    project_id: str,
    timeline_service: TimelineSettingsService = Depends(get_timeline_service),
) -> MusicTrackListResponse:
    tracks = await timeline_service.list_music_tracks(project_id)
    return MusicTrackListResponse(
        tracks=[MusicTrackResponse.model_validate(track.model_dump()) for track in tracks]
    )


@router.get("/music", response_model=MusicSettingsResponse)
async def get_music_settings(
    project_id: str,
    timeline_service: TimelineSettingsService = Depends(get_timeline_service),
) -> MusicSettingsResponse:
    settings = await timeline_service.get_settings(project_id)
    return MusicSettingsResponse(
        **_serialize_music_settings(settings.music).model_dump(),
        updated_at=settings.updated_at,
    )


@router.put("/music", response_model=MusicSettingsResponse, status_code=status.HTTP_200_OK)
async def update_music(
    project_id: str,
    request: MusicSettingsPayload,
    timeline_service: TimelineSettingsService = Depends(get_timeline_service),
) -> MusicSettingsResponse:
    try:
        settings = await timeline_service.update_music_settings(project_id, request.model_dump())
    except ValueError as exc:  # Track not found or validation error from service
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return MusicSettingsResponse(
        **_serialize_music_settings(settings.music).model_dump(),
        updated_at=settings.updated_at,
    )
