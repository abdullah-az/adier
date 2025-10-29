from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from ..models.enums import ProjectStatus
from .base import TimestampedSchema


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    storage_path: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    storage_path: Optional[str] = None


class ProjectRead(ProjectBase, TimestampedSchema):
    pass


__all__ = [
    "ProjectBase",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectRead",
]
