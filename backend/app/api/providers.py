"""API endpoints for managing AI providers and overrides."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_ai_orchestrator
from app.schemas.provider import (
    ProviderListResponse,
    ProviderOverrideRequest,
    ProviderPriorityResponse,
    ProviderPriorityUpdateRequest,
    ProviderPriorityUpdateResponse,
    ProviderUsageEntry,
    ProviderUsageSummaryResponse,
)
from app.services.ai import AIOrchestrator

router = APIRouter(prefix="/providers", tags=["providers"])


def _ensure_known_providers(orchestrator: AIOrchestrator, provider_ids: list[str]) -> None:
    unknown = [provider_id for provider_id in provider_ids if provider_id not in orchestrator.providers]
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown provider(s): {', '.join(sorted(unknown))}",
        )


@router.get("", response_model=ProviderListResponse)
async def list_providers(orchestrator: AIOrchestrator = Depends(get_ai_orchestrator)) -> ProviderListResponse:
    entries = orchestrator.list_providers(include_unconfigured=True)
    providers = [
        {
            "id": entry["id"],
            "name": entry["name"],
            "capabilities": entry.get("capabilities", []),
            "configured": entry.get("configured", False),
            "available": entry.get("available", False),
            "priority_rank": entry.get("priority_rank"),
            "usage": entry.get("usage", {}),
            "currency": entry.get("currency"),
            "rate_limits": entry.get("rate_limits", {}),
        }
        for entry in entries
    ]
    return ProviderListResponse(providers=providers)


@router.get("/usage", response_model=ProviderUsageSummaryResponse)
async def usage_summary(orchestrator: AIOrchestrator = Depends(get_ai_orchestrator)) -> ProviderUsageSummaryResponse:
    summary = orchestrator.get_usage_summary()
    providers = [
        ProviderUsageEntry(
            provider_id=provider_id,
            requests=stats.get("requests", 0),
            cost=float(stats.get("cost", 0.0)),
            currency=orchestrator.currency,
            last_used=stats.get("last_used"),
            tokens=int(stats.get("tokens", 0) or 0),
            tasks=stats.get("tasks", {}),
        )
        for provider_id, stats in summary.items()
    ]
    providers.sort(key=lambda item: item.provider_id)
    return ProviderUsageSummaryResponse(providers=providers)


@router.get("/priority", response_model=ProviderPriorityResponse)
async def get_global_priority(orchestrator: AIOrchestrator = Depends(get_ai_orchestrator)) -> ProviderPriorityResponse:
    return ProviderPriorityResponse(priority=orchestrator.get_priority())


@router.put("/priority", response_model=ProviderPriorityUpdateResponse)
async def update_global_priority(
    request: ProviderPriorityUpdateRequest,
    orchestrator: AIOrchestrator = Depends(get_ai_orchestrator),
) -> ProviderPriorityUpdateResponse:
    _ensure_known_providers(orchestrator, request.priority)
    updated = await orchestrator.update_priority(request.priority)
    return ProviderPriorityUpdateResponse(priority=updated)


@router.get("/projects/{project_id}", response_model=ProviderPriorityResponse)
async def get_project_priority(
    project_id: str,
    orchestrator: AIOrchestrator = Depends(get_ai_orchestrator),
) -> ProviderPriorityResponse:
    overrides = orchestrator.get_project_overrides(project_id)
    return ProviderPriorityResponse(**overrides)


@router.put("/projects/{project_id}", response_model=ProviderPriorityResponse)
async def update_project_priority(
    project_id: str,
    request: ProviderOverrideRequest,
    orchestrator: AIOrchestrator = Depends(get_ai_orchestrator),
) -> ProviderPriorityResponse:
    priority = request.priority
    task_overrides = request.task_overrides

    if priority is not None:
        _ensure_known_providers(orchestrator, priority)
    if task_overrides:
        for chain in task_overrides.values():
            _ensure_known_providers(orchestrator, chain)

    overrides = await orchestrator.set_project_overrides(
        project_id,
        priority=priority,
        task_overrides=task_overrides,
    )
    return ProviderPriorityResponse(**overrides)
