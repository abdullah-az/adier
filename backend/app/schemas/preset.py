from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from ..models.enums import PresetCategory
from .base import TimestampedSchema


class PresetBase(BaseModel):
    key: str
    name: str
    category: PresetCategory
    description: Optional[str] = None
    configuration: dict[str, object]


class PresetCreate(PresetBase):
    pass


class PresetUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[PresetCategory] = None
    description: Optional[str] = None
    configuration: Optional[dict[str, object]] = None


class PresetRead(PresetBase, TimestampedSchema):
    pass


__all__ = [
    "PresetBase",
    "PresetCreate",
    "PresetUpdate",
    "PresetRead",
]
