from __future__ import annotations

from .base import SQLAlchemyRepository
from ..models.project import Project


class ProjectRepository(SQLAlchemyRepository[Project]):
    model_cls = Project


__all__ = ["ProjectRepository"]
