from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_ai_manager
from app.schemas.ai import (
    ProviderInfoResponse,
    ProviderPreferenceResponse,
    ProviderPreferenceUpdate,
)
from app.services.ai.manager import AIManager

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/providers", response_model=list[ProviderInfoResponse])
async def list_ai_providers(ai_manager: AIManager = Depends(get_ai_manager)) -> list[ProviderInfoResponse]:
    providers = await ai_manager.list_providers()
    return [ProviderInfoResponse.model_validate(provider) for provider in providers]


@router.get(
    "/projects/{project_id}/providers/preferences",
    response_model=ProviderPreferenceResponse,
)
async def get_project_preferences(
    project_id: str,
    ai_manager: AIManager = Depends(get_ai_manager),
) -> ProviderPreferenceResponse:
    preferences = await ai_manager.get_preferences(project_id)
    return ProviderPreferenceResponse(project_id=project_id, preferences=preferences)


@router.put(
    "/projects/{project_id}/providers/preferences",
    response_model=ProviderPreferenceResponse,
    status_code=status.HTTP_200_OK,
)
async def set_project_preferences(
    project_id: str,
    request: ProviderPreferenceUpdate,
    ai_manager: AIManager = Depends(get_ai_manager),
) -> ProviderPreferenceResponse:
    preferences = await ai_manager.set_preferences(project_id, request.preferences)
    return ProviderPreferenceResponse(project_id=project_id, preferences=preferences)
