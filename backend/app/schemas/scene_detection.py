from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SceneDetectionBase(BaseModel):
    label: Optional[str] = Field(default=None, max_length=255)
    start_time: float = Field(..., ge=0)
    end_time: float = Field(..., gt=0)
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_timing(self) -> "SceneDetectionBase":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be greater than start_time")
        return self


class SceneDetectionCreate(SceneDetectionBase):
    project_id: str = Field(..., min_length=1)
    video_asset_id: str = Field(..., min_length=1)


class SceneDetectionUpdate(BaseModel):
    label: Optional[str] = Field(default=None, max_length=255)
    start_time: Optional[float] = Field(default=None, ge=0)
    end_time: Optional[float] = Field(default=None, gt=0)
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    metadata: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def _check_timing(self) -> "SceneDetectionUpdate":
        if self.start_time is not None and self.end_time is not None:
            if self.end_time <= self.start_time:
                raise ValueError("end_time must be greater than start_time")
        return self


class SceneDetectionRead(SceneDetectionBase):
    id: str
    project_id: str
    video_asset_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
