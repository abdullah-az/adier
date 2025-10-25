from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_ai_service
from app.schemas.ai import SceneSuggestion, SceneSuggestionRequest, SceneSuggestionResponse
from app.schemas.common import ApiResponse
from app.services.ai_suggestion_service import AiSuggestionService, SceneSuggestionError
from app.utils.responses import error_response, success_response

router = APIRouter(prefix="/projects/{project_id}/ai", tags=["ai"])


@router.post(
    "/suggestions",
    response_model=ApiResponse[SceneSuggestionResponse],
    summary="Generate AI-assisted scene suggestions",
)
async def generate_scene_suggestions(
    project_id: str,
    payload: SceneSuggestionRequest,
    ai_service: AiSuggestionService = Depends(get_ai_service),
) -> ApiResponse[SceneSuggestionResponse]:
    try:
        suggestions = await ai_service.suggest_scenes(
            project_id,
            payload.asset_id,
            locale=payload.locale,
            max_suggestions=payload.max_suggestions,
            target_duration=payload.target_duration,
            focus_keywords=payload.focus_keywords,
        )
    except SceneSuggestionError as exc:
        return error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="SCENE_SUGGESTION_FAILED",
            message=str(exc),
        )

    response = SceneSuggestionResponse(
        suggestions=[SceneSuggestion(**suggestion) for suggestion in suggestions]
    )
    return success_response(response, message="Scene suggestions generated", code="SCENE_SUGGESTIONS_READY")
