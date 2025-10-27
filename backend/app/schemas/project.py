from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.project import ProjectStatus, TimelineState
from app.schemas.common import PaginationMeta


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., description="Human readable project name", example="Launch Teaser Vertical")
    description: Optional[str] = Field(default=None, example="60s teaser for social channels")
    primary_locale: str = Field(default="en-US", example="en-US")
    supported_locales: list[str] = Field(default_factory=list, example=["en-US", "ar-SA"])
    tags: list[str] = Field(default_factory=list, example=["launch", "social", "vertical"])
    metadata: dict[str, Any] = Field(default_factory=dict, example={"client": "Acme"})
    project_id: Optional[str] = Field(default=None, example="launch-2024")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Launch Teaser Vertical",
                "description": "60s teaser for social channels",
                "primary_locale": "en-US",
                "supported_locales": ["en-US", "ar-SA"],
                "tags": ["launch", "social"],
                "metadata": {"client": "Acme Corp", "owner": "marketing"},
            }
        }
    }


class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    status: Optional[ProjectStatus] = Field(default=None)
    primary_locale: Optional[str] = Field(default=None)
    supported_locales: Optional[list[str]] = Field(default=None)
    tags: Optional[list[str]] = Field(default=None)
    metadata: Optional[dict[str, Any]] = Field(default=None)


class ProjectSummary(BaseModel):
    id: str
    name: str
    status: ProjectStatus
    updated_at: datetime
    primary_locale: str
    thumbnail_url: Optional[str] = None


class ProjectListResponse(BaseModel):
    items: list[ProjectSummary]
    pagination: PaginationMeta


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: ProjectStatus
    primary_locale: str
    supported_locales: list[str]
    tags: list[str]
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    timeline: Optional[TimelineState] = None

    model_config = {"json_schema_extra": {"example": {
        "id": "launch-2024",
        "name": "Launch Teaser Vertical",
        "description": "60s teaser for social channels",
        "status": "editing",
        "primary_locale": "en-US",
        "supported_locales": ["en-US", "ar-SA"],
        "tags": ["launch", "social"],
        "metadata": {"client": "Acme Corp"},
        "created_at": "2024-10-12T08:15:23.000Z",
        "updated_at": "2024-10-12T09:05:12.000Z",
        "timeline": None,
    }}}
