from __future__ import annotations

from .base import SQLAlchemyRepository
from ..models.processing_job import ProcessingJob


class ProcessingJobRepository(SQLAlchemyRepository[ProcessingJob]):
    model_cls = ProcessingJob


__all__ = ["ProcessingJobRepository"]
