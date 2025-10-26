from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    frame_rate: float = Field(default=24.0, gt=0, le=240)
    resolution_width: int = Field(default=1920, ge=1, le=8192)
    resolution_height: int = Field(default=1080, ge=1, le=8192)
    duration_seconds: float = Field(default=0.0, ge=0)
    thumbnail_path: Optional[str] = Field(default=None, max_length=512)
    color_profile: Optional[str] = Field(default=None, max_length=64)

    @field_validator("slug")
    @classmethod
    def _validate_slug(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        slug = value.strip().lower()
        if not slug:
            raise ValueError("slug cannot be empty when provided")
        if not re.fullmatch(r"[a-z0-9-]+", slug):
            raise ValueError("slug must contain only lowercase letters, numbers, or hyphens")
        return slug


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    slug: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    frame_rate: Optional[float] = Field(default=None, gt=0, le=240)
    resolution_width: Optional[int] = Field(default=None, ge=1, le=8192)
    resolution_height: Optional[int] = Field(default=None, ge=1, le=8192)
    duration_seconds: Optional[float] = Field(default=None, ge=0)
    thumbnail_path: Optional[str] = Field(default=None, max_length=512)
    color_profile: Optional[str] = Field(default=None, max_length=64)

    @field_validator("slug")
    @classmethod
    def _validate_slug(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        slug = value.strip().lower()
        if not slug:
            raise ValueError("slug cannot be empty when provided")
        if not re.fullmatch(r"[a-z0-9-]+", slug):
            raise ValueError("slug must contain only lowercase letters, numbers, or hyphens")
        return slug


class ProjectRead(ProjectBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
