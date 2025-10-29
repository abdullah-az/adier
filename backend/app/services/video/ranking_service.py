from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field

from ...models.clip import ClipVersion
from ...repositories.clip import ClipVersionRepository
from ..ai.analysis_service import SceneScore


@dataclass(frozen=True)
class RankingWeights:
    quality: float = 0.5
    ai_score: float = 0.5

    def normalised(self) -> tuple[float, float]:
        components = [max(self.quality, 0.0), max(self.ai_score, 0.0)]
        total = sum(components)
        if total <= 0:
            return (1.0, 0.0)
        return tuple(component / total for component in components)


class ClipRanking(BaseModel):
    clip_version_id: str
    quality_score: float
    ai_score: float | None
    combined_score: float
    quality_metrics: Dict[str, float | None] | None = None
    recommendation: str

    model_config = ConfigDict(frozen=True)


class RetakeSuggestion(BaseModel):
    clip_version_id: str
    issues: List[str]
    quality_score: float
    quality_metrics: Dict[str, float | None] | None = None

    model_config = ConfigDict(frozen=True)


class RankingService:
    def __init__(
        self,
        repository: ClipVersionRepository,
        *,
        weights: RankingWeights | None = None,
        quality_threshold: float = 0.6,
        logger: logging.Logger | None = None,
    ) -> None:
        self._repository = repository
        self._weights = weights or RankingWeights()
        self._quality_threshold = quality_threshold
        self._logger = logger or logging.getLogger("backend.app.services.video.ranking")

    def rank_clips(
        self,
        clip_versions: Sequence[ClipVersion],
        *,
        scene_scores: Optional[Dict[str, SceneScore]] = None,
    ) -> List[ClipRanking]:
        rankings: List[ClipRanking] = []
        quality_weight, ai_weight = self._weights.normalised()

        for version in clip_versions:
            quality_metrics = version.quality_metrics or {}
            quality_score = quality_metrics.get("overall_score", 0.0)

            ai_score: float | None = None
            if scene_scores and version.clip.source_asset_id:
                scene_id = self._get_scene_id_for_version(version)
                if scene_id and scene_id in scene_scores:
                    ai_score = scene_scores[scene_id].highlight_score

            if ai_score is not None:
                combined = quality_score * quality_weight + ai_score * ai_weight
            else:
                combined = quality_score

            recommendation = self._generate_recommendation(quality_score, ai_score, combined)

            rankings.append(
                ClipRanking(
                    clip_version_id=version.id,
                    quality_score=quality_score,
                    ai_score=ai_score,
                    combined_score=combined,
                    quality_metrics=quality_metrics,
                    recommendation=recommendation,
                )
            )

        rankings.sort(key=lambda r: r.combined_score, reverse=True)
        return rankings

    def get_top_clips(
        self,
        clip_versions: Sequence[ClipVersion],
        *,
        top_n: int = 5,
        scene_scores: Optional[Dict[str, SceneScore]] = None,
    ) -> List[ClipRanking]:
        rankings = self.rank_clips(clip_versions, scene_scores=scene_scores)
        return rankings[:top_n]

    def suggest_retakes(
        self,
        clip_versions: Sequence[ClipVersion],
        *,
        quality_threshold: float | None = None,
    ) -> List[RetakeSuggestion]:
        threshold = quality_threshold if quality_threshold is not None else self._quality_threshold
        suggestions: List[RetakeSuggestion] = []

        for version in clip_versions:
            quality_metrics = version.quality_metrics or {}
            quality_score = quality_metrics.get("overall_score", 0.0)

            if quality_score < threshold:
                issues = self._identify_quality_issues(quality_metrics)
                suggestions.append(
                    RetakeSuggestion(
                        clip_version_id=version.id,
                        issues=issues,
                        quality_score=quality_score,
                        quality_metrics=quality_metrics,
                    )
                )

        suggestions.sort(key=lambda s: s.quality_score)
        return suggestions

    def _generate_recommendation(
        self,
        quality_score: float,
        ai_score: float | None,
        combined_score: float,
    ) -> str:
        if combined_score >= 0.8:
            return "Excellent - Ready for publication"
        elif combined_score >= 0.6:
            return "Good - Minor improvements possible"
        elif combined_score >= 0.4:
            return "Fair - Consider improvements"
        else:
            return "Poor - Retake recommended"

    def _identify_quality_issues(self, quality_metrics: Dict[str, float | None]) -> List[str]:
        issues: List[str] = []

        sharpness = quality_metrics.get("sharpness", 1.0)
        if sharpness is not None and sharpness < 0.5:
            issues.append(f"Low sharpness (score: {sharpness:.2f})")

        exposure = quality_metrics.get("exposure", 1.0)
        if exposure is not None and exposure < 0.5:
            issues.append(f"Poor exposure (score: {exposure:.2f})")

        motion_blur = quality_metrics.get("motion_blur", 0.0)
        if motion_blur is not None and motion_blur > 0.5:
            issues.append(f"High motion blur (score: {motion_blur:.2f})")

        noise_level = quality_metrics.get("noise_level", 1.0)
        if noise_level is not None and noise_level < 0.5:
            issues.append(f"High noise level (score: {noise_level:.2f})")

        audio_quality = quality_metrics.get("audio_quality")
        if audio_quality is not None and audio_quality < 0.5:
            issues.append(f"Poor audio quality (score: {audio_quality:.2f})")

        if not issues:
            issues.append("Overall quality below threshold")

        return issues

    def _get_scene_id_for_version(self, version: ClipVersion) -> str | None:
        if version.clip.start_time is not None:
            return f"scene_{int(version.clip.start_time)}"
        return None


__all__ = ["RankingService", "RankingWeights", "ClipRanking", "RetakeSuggestion"]
