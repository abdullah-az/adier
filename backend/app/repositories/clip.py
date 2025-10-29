from __future__ import annotations

from .base import SQLAlchemyRepository
from ..models.clip import Clip, ClipVersion


class ClipRepository(SQLAlchemyRepository[Clip]):
    model_cls = Clip


class ClipVersionRepository(SQLAlchemyRepository[ClipVersion]):
    model_cls = ClipVersion


__all__ = ["ClipRepository", "ClipVersionRepository"]
