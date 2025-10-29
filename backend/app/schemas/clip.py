from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from ..models.enums import ClipStatus, ClipVersionStatus
from .base import TimestampedSchema


class ClipBase(BaseModel):
    project_id: str
    source_asset_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: ClipStatus = ClipStatus.DRAFT
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class ClipCreate(ClipBase):
    pass


class ClipUpdate(BaseModel):
    source_asset_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ClipStatus] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class ClipRead(ClipBase, TimestampedSchema):
    pass


class ClipVersionBase(BaseModel):
    clip_id: str
    output_asset_id: Optional[str] = None
    preset_id: Optional[str] = None
    version_number: int = 1
    status: ClipVersionStatus = ClipVersionStatus.DRAFT
    notes: Optional[str] = None


class ClipVersionCreate(ClipVersionBase):
    pass


class ClipVersionUpdate(BaseModel):
    output_asset_id: Optional[str] = None
    preset_id: Optional[str] = None
    version_number: Optional[int] = None
    status: Optional[ClipVersionStatus] = None
    notes: Optional[str] = None


class ClipVersionRead(ClipVersionBase, TimestampedSchema):
    pass


__all__ = [
    "ClipBase",
    "ClipCreate",
    "ClipUpdate",
    "ClipRead",
    "ClipVersionBase",
    "ClipVersionCreate",
    "ClipVersionUpdate",
    "ClipVersionRead",
]
