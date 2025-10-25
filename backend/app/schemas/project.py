from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, constr

from app.models.enums import ProjectStatus


class ProjectBase(BaseModel):
    name: constr(min_length=1, max_length=255) = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    status: ProjectStatus = Field(default=ProjectStatus.DRAFT, description="Project status")
    thumbnail_path: Optional[str] = Field(None, max_length=512, description="Path to project thumbnail")
    duration: Optional[float] = Field(None, ge=0, description="Project duration in seconds")
    project_metadata: Optional[dict] = Field(None, description="Project metadata as JSON")
    settings: Optional[dict] = Field(None, description="Project settings as JSON")


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[constr(min_length=1, max_length=255)] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    thumbnail_path: Optional[str] = Field(None, max_length=512)
    duration: Optional[float] = Field(None, ge=0)
    project_metadata: Optional[dict] = None
    settings: Optional[dict] = None


class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
