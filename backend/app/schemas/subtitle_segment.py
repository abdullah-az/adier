from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SubtitleSegmentBase(BaseModel):
    language: str = Field(default="en", min_length=2, max_length=16)
    speaker: Optional[str] = Field(default=None, max_length=128)
    start_time: float = Field(..., ge=0)
    end_time: float = Field(..., gt=0)
    text: str = Field(..., min_length=1)
    is_approved: bool = Field(default=False)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("language")
    @classmethod
    def _normalise_language(cls, value: str) -> str:
        lang = value.strip().lower()
        if len(lang) < 2:
            raise ValueError("language code is too short")
        return lang

    @model_validator(mode="after")
    def _check_timing(self) -> "SubtitleSegmentBase":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be greater than start_time")
        return self


class SubtitleSegmentCreate(SubtitleSegmentBase):
    project_id: str = Field(..., min_length=1)
    video_asset_id: Optional[str] = Field(default=None, min_length=1)


class SubtitleSegmentUpdate(BaseModel):
    language: Optional[str] = Field(default=None, min_length=2, max_length=16)
    speaker: Optional[str] = Field(default=None, max_length=128)
    start_time: Optional[float] = Field(default=None, ge=0)
    end_time: Optional[float] = Field(default=None, gt=0)
    text: Optional[str] = Field(default=None, min_length=1)
    is_approved: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("language")
    @classmethod
    def _normalise_language(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        lang = value.strip().lower()
        if len(lang) < 2:
            raise ValueError("language code is too short")
        return lang

    @model_validator(mode="after")
    def _check_timing(self) -> "SubtitleSegmentUpdate":
        if self.start_time is not None and self.end_time is not None:
            if self.end_time <= self.start_time:
                raise ValueError("end_time must be greater than start_time")
        return self


class SubtitleSegmentRead(SubtitleSegmentBase):
    id: str
    project_id: str
    video_asset_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
