from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from app.repositories.video_repository import VideoAssetRepository


class AISuggestionService:
    """Generate deterministic AI-like suggestions derived from stored asset metadata."""

    def __init__(self, video_repository: VideoAssetRepository) -> None:
        self.video_repository = video_repository

    async def generate_scene_suggestions(
        self,
        project_id: str,
        *,
        locale: str,
        limit: int = 10,
    ) -> dict[str, Any]:
        assets = await self.video_repository.list_by_project(project_id)
        if not assets:
            return {
                "locale": locale,
                "generated_at": datetime.utcnow().isoformat(),
                "scenes": [],
                "source_assets": [],
            }

        limit = max(1, min(limit, 25))
        suggestions: list[dict[str, Any]] = []
        source_assets: list[dict[str, Any]] = []
        for asset in assets:
            duration_raw = None
            if asset.metadata:
                try:
                    duration_raw = float(asset.metadata.get("duration"))
                except (TypeError, ValueError):  # pragma: no cover - defensive
                    duration_raw = None
            size_mb = (asset.size_bytes or 0) / (1024 * 1024)
            duration = duration_raw or max(size_mb / 2 if size_mb else 1.0, 1.0)
            slices = max(1, min(5, int(duration // 5) or 1))
            segment_length = max(duration / (slices + 1), 3.0)
            source_assets.append(
                {
                    "asset_id": asset.id,
                    "duration": duration,
                    "filename": asset.original_filename,
                }
            )
            for index in range(slices):
                if len(suggestions) >= limit:
                    break
                start = round(min(duration * 0.8, index * segment_length), 2)
                end = round(min(duration, start + segment_length), 2)
                confidence = round(0.7 + (0.3 / (index + 1)), 3)
                suggestions.append(
                    {
                        "scene_id": uuid4().hex,
                        "asset_id": asset.id,
                        "start": start,
                        "end": end,
                        "duration": round(max(end - start, 0.5), 2),
                        "confidence": min(confidence, 0.99),
                        "locale": locale,
                        "title": f"Highlight {index + 1} from {asset.original_filename}",
                        "description": "Automatically detected high-impact moment suitable for vertical storytelling.",
                        "tags": ["ai", "suggested", "scene"],
                        "metadata": {
                            "source_duration": duration,
                            "rank": len(suggestions) + 1,
                        },
                    }
                )
            if len(suggestions) >= limit:
                break

        return {
            "locale": locale,
            "generated_at": datetime.utcnow().isoformat(),
            "scenes": suggestions[:limit],
            "source_assets": source_assets,
        }
