from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_scene_repository, get_transcript_repository
from app.repositories.scene_repository import SceneAnalysisRepository
from app.repositories.transcript_repository import TranscriptRepository
from app.schemas.scene import SceneAnalysisListResponse, SceneAnalysisResponse
from app.schemas.transcript import TranscriptResponse

router = APIRouter(prefix="/projects/{project_id}", tags=["ai"])


@router.get("/ai/scenes", response_model=SceneAnalysisListResponse)
async def list_project_scenes(
    project_id: str,
    scene_repository: SceneAnalysisRepository = Depends(get_scene_repository),
) -> SceneAnalysisListResponse:
    analyses = await scene_repository.list_by_project(project_id)
    return SceneAnalysisListResponse(
        analyses=[SceneAnalysisResponse.from_model(item) for item in analyses],
    )


@router.get("/videos/{asset_id}/scenes", response_model=list[SceneAnalysisResponse])
async def list_scenes_for_asset(
    project_id: str,
    asset_id: str,
    scene_repository: SceneAnalysisRepository = Depends(get_scene_repository),
) -> list[SceneAnalysisResponse]:
    analyses = await scene_repository.list_by_asset(asset_id)
    filtered = [analysis for analysis in analyses if analysis.project_id == project_id]
    return [SceneAnalysisResponse.from_model(item) for item in filtered]


@router.get("/videos/{asset_id}/transcript", response_model=TranscriptResponse)
async def get_transcript_for_asset(
    project_id: str,
    asset_id: str,
    transcript_repository: TranscriptRepository = Depends(get_transcript_repository),
) -> TranscriptResponse:
    transcript = await transcript_repository.get_by_asset(asset_id)
    if transcript is None or transcript.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found")
    return TranscriptResponse.from_model(transcript)
