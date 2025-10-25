from __future__ import annotations

from typing import Any, List, Optional

from loguru import logger

from app.repositories.video_repository import VideoAssetRepository


class SceneSuggestionError(ValueError):
    """Raised when AI scene suggestion inputs are invalid."""


class AiSuggestionService:
    """Generate AI-driven scene suggestions using asset metadata stubs."""

    def __init__(self, video_repository: VideoAssetRepository) -> None:
        self.video_repository = video_repository

    async def suggest_scenes(
        self,
        project_id: str,
        asset_id: str,
        *,
        locale: str = "en",
        max_suggestions: int = 5,
        target_duration: Optional[float] = None,
        focus_keywords: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        asset = await self.video_repository.get(asset_id)
        if asset is None or asset.project_id != project_id:
            raise SceneSuggestionError("Asset not found in project")
        if max_suggestions <= 0:
            raise SceneSuggestionError("max_suggestions must be greater than zero")

        metadata = asset.metadata or {}
        duration = float(metadata.get("duration") or metadata.get("runtime") or target_duration or 60.0)
        duration = max(duration, float(max_suggestions))
        segment_length = duration / max_suggestions
        suggestions: list[dict[str, Any]] = []

        keywords = focus_keywords or metadata.get("keywords") or []
        transcript = metadata.get("transcript")

        logger.debug(
            "Generating scene suggestions",
            asset_id=asset_id,
            project_id=project_id,
            suggestions=max_suggestions,
            duration=duration,
        )

        for index in range(max_suggestions):
            start = round(index * segment_length, 2)
            end = round(min(duration, (index + 1) * segment_length), 2)
            suggestions.append(
                {
                    "id": f"{asset_id}-scene-{index + 1}",
                    "asset_id": asset_id,
                    "start": start,
                    "end": end,
                    "confidence": round(0.65 + 0.05 * (max_suggestions - index), 2),
                    "title": f"Scene {index + 1}",
                    "description": self._build_description(start, end, keywords, transcript),
                    "locale": locale,
                    "keywords": keywords,
                }
            )

        return suggestions

    def _build_description(
        self,
        start: float,
        end: float,
        keywords: list[str] | None,
        transcript: Optional[str],
    ) -> str:
        keyword_part = f" Keywords: {', '.join(keywords)}." if keywords else ""
        transcript_part = "" if not transcript else " Transcript snippet: " + transcript[:120].strip() + "..."
        return f"Auto-suggested scene spanning {start:.2f}s to {end:.2f}s." + keyword_part + transcript_part
