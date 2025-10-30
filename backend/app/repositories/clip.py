from __future__ import annotations

from typing import Any, Dict

from .base import SQLAlchemyRepository
from ..models.clip import Clip, ClipVersion


class ClipRepository(SQLAlchemyRepository[Clip]):
    model_cls = Clip


class ClipVersionRepository(SQLAlchemyRepository[ClipVersion]):
    model_cls = ClipVersion

    def update_quality_metrics(self, version: ClipVersion, metrics: Dict[str, Any]) -> ClipVersion:
        version.quality_metrics = metrics
        self.session.add(version)
        self.session.commit()
        self.session.refresh(version)
        return version

    def get_versions_by_quality_threshold(
        self, project_id: str, threshold: float, *, limit: int = 100
    ) -> list[ClipVersion]:
        from sqlalchemy import and_, func
        from ..models.clip import Clip

        query = (
            self.session.query(ClipVersion)
            .join(Clip)
            .filter(
                and_(
                    Clip.project_id == project_id,
                    func.json_extract(ClipVersion.quality_metrics, "$.overall_score") >= threshold,
                )
            )
            .limit(limit)
        )
        return query.all()


__all__ = ["ClipRepository", "ClipVersionRepository"]
