from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_scene_repository,
    get_subtitle_repository,
    get_video_repository,
)
from app.models.scene_detection import SceneDetectionRun
from app.models.subtitle import SubtitleSegment, SubtitleTranscript
from app.repositories.scene_repository import SceneDetectionRepository
from app.repositories.subtitle_repository import SubtitleRepository
from app.repositories.video_repository import VideoAssetRepository
from app.schemas.ai import (
    SceneDetectionResponse,
    SceneDetectionSchema,
    SubtitleSegmentSchema,
    SubtitleTranscriptResponse,
)

router = APIRouter(prefix="/projects/{project_id}/videos/{asset_id}/ai", tags=["ai"])


async def _ensure_asset(
    project_id: str,
    asset_id: str,
    repository: VideoAssetRepository,
) -> None:
    asset = await repository.get(asset_id)
    if asset is None or asset.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video asset not found")


def _segment_to_schema(segment: SubtitleSegment) -> SubtitleSegmentSchema:
    return SubtitleSegmentSchema(
        index=segment.index,
        start=segment.start,
        end=segment.end,
        duration=segment.duration,
        text=segment.text,
        confidence=segment.confidence,
        language=segment.language,
        speaker=segment.speaker,
    )


def _transcript_to_response(transcript: SubtitleTranscript) -> SubtitleTranscriptResponse:
    return SubtitleTranscriptResponse(
        asset_id=transcript.asset_id,
        project_id=transcript.project_id,
        request_id=transcript.id,
        language=transcript.language,
        text=transcript.text,
        segment_count=transcript.segment_count,
        duration=transcript.duration,
        usage=transcript.usage or {},
        segments=[_segment_to_schema(segment) for segment in transcript.segments],
        cached=transcript.cached,
        created_at=transcript.created_at,
        updated_at=transcript.updated_at,
        metadata=transcript.metadata,
    )


def _scene_to_schema(scene_run: SceneDetectionRun) -> SceneDetectionResponse:
    scenes = sorted(
        scene_run.scenes,
        key=lambda item: (item.priority or 0, item.start),
    )
    return SceneDetectionResponse(
        asset_id=scene_run.asset_id,
        project_id=scene_run.project_id,
        request_id=scene_run.id,
        generated_at=scene_run.generated_at,
        parameters=scene_run.parameters,
        usage=scene_run.usage,
        metadata=scene_run.metadata,
        scenes=[
            SceneDetectionSchema(
                id=scene.id,
                title=scene.title,
                description=scene.description,
                start=scene.start,
                end=scene.end,
                duration=scene.duration,
                confidence=scene.confidence,
                priority=scene.priority,
                tags=scene.tags,
                metadata=scene.metadata,
            )
            for scene in scenes
        ],
    )


@router.get("/transcript", response_model=SubtitleTranscriptResponse)
async def get_transcript(
    project_id: str,
    asset_id: str,
    video_repository: VideoAssetRepository = Depends(get_video_repository),
    subtitle_repository: SubtitleRepository = Depends(get_subtitle_repository),
) -> SubtitleTranscriptResponse:
    await _ensure_asset(project_id, asset_id, video_repository)
    transcript = await subtitle_repository.get_transcript(asset_id)
    if transcript is None or transcript.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found")
    return _transcript_to_response(transcript)


@router.get("/scenes", response_model=SceneDetectionResponse)
async def get_scene_suggestions(
    project_id: str,
    asset_id: str,
    video_repository: VideoAssetRepository = Depends(get_video_repository),
    scene_repository: SceneDetectionRepository = Depends(get_scene_repository),
) -> SceneDetectionResponse:
    await _ensure_asset(project_id, asset_id, video_repository)
    scene_run = await scene_repository.get_latest(asset_id)
    if scene_run is None or scene_run.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene analysis not available")
    return _scene_to_schema(scene_run)


__all__ = ["router"]
