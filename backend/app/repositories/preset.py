from __future__ import annotations

from .base import SQLAlchemyRepository
from ..models.preset import Preset


class PresetRepository(SQLAlchemyRepository[Preset]):
    model_cls = Preset


__all__ = ["PresetRepository"]
