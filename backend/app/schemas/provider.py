"""Schemas for AI provider configuration and reporting."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.services.ai import ProviderTask


class ProviderInfo(BaseModel):
    id: str
    name: str
    capabilities: List[str]
    configured: bool
    available: bool
    priority_rank: Optional[int] = None
    usage: Dict[str, Any] = Field(default_factory=dict)
    currency: str
    rate_limits: Dict[str, Any] = Field(default_factory=dict)


class ProviderUsageEntry(BaseModel):
    provider_id: str
    requests: int
    cost: float
    currency: str
    last_used: Optional[datetime] = None
    tokens: int = 0
    tasks: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class ProviderUsageSummaryResponse(BaseModel):
    providers: List[ProviderUsageEntry]


class ProviderListResponse(BaseModel):
    providers: List[ProviderInfo]


class ProviderPriorityResponse(BaseModel):
    priority: List[str] = Field(default_factory=list)
    task_overrides: Dict[str, List[str]] = Field(default_factory=dict)


class ProviderOverrideRequest(BaseModel):
    priority: Optional[List[str]] = None
    task_overrides: Optional[Dict[str, List[str]]] = None

    @field_validator("task_overrides")
    @classmethod
    def _validate_tasks(cls, value: Optional[Dict[str, List[str]]]) -> Optional[Dict[str, List[str]]]:
        if value is None:
            return None
        validated: Dict[str, List[str]] = {}
        for task_name, chain in value.items():
            ProviderTask(task_name)  # Raises ValueError if unsupported
            validated[ProviderTask(task_name).value] = chain
        return validated


class ProviderPriorityUpdateRequest(BaseModel):
    priority: List[str]


class ProviderPriorityUpdateResponse(BaseModel):
    priority: List[str]
