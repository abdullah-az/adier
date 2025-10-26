from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Optional

from loguru import logger

from app.core.config import Settings
from app.models.scene_detection import SceneDetection, SceneDetectionRun
from app.repositories.scene_repository import SceneDetectionRepository
from app.repositories.subtitle_repository import SubtitleRepository
from app.repositories.video_repository import VideoAssetRepository
from app.services.exceptions import (
    AIMissingConfigurationError,
    AINonRetryableError,
    AIRetryableError,
)
from app.services.openai_client import OpenAIClient
from app.services.prompt_templates import build_scene_detection_messages


class SceneAnalysisService:
    """Generate highlight recommendations from transcripts using OpenAI."""

    def __init__(
        self,
        *,
        settings: Settings,
        video_repository: VideoAssetRepository,
        subtitle_repository: SubtitleRepository,
        scene_repository: SceneDetectionRepository,
        openai_client: OpenAIClient,
    ) -> None:
        self.settings = settings
        self.video_repository = video_repository
        self.subtitle_repository = subtitle_repository
        self.scene_repository = scene_repository
        self.openai_client = openai_client
        self.model = settings.openai_scene_model
        self.default_max_scenes = max(1, settings.openai_scene_max_scenes)

    async def detect_scenes(
        self,
        *,
        project_id: str,
        asset_id: str,
        tone: Optional[str] = None,
        highlight_criteria: Optional[str] = None,
        max_scenes: Optional[int] = None,
        force: bool = False,
        extra_instructions: Optional[str] = None,
    ) -> SceneDetectionRun:
        asset = await self.video_repository.get(asset_id)
        if asset is None or asset.project_id != project_id:
            raise AINonRetryableError("Video asset not found for scene analysis", context={"asset_id": asset_id})

        transcript = await self.subtitle_repository.get_transcript(asset_id)
        if transcript is None:
            raise AINonRetryableError(
                "Transcript is required before running scene detection",
                context={"asset_id": asset_id},
            )

        if not self.settings.openai_api_key:
            raise AIMissingConfigurationError("OpenAI scene analysis requires OPENAI_API_KEY")

        if max_scenes is not None:
            try:
                max_items = max(1, int(max_scenes))
            except (TypeError, ValueError):
                max_items = self.default_max_scenes
        else:
            max_items = self.default_max_scenes
        request_hash = self._request_hash(tone=tone, criteria=highlight_criteria, max_scenes=max_items)

        existing = await self.scene_repository.get_latest(asset_id)
        if existing and not force:
            if existing.metadata.get("request_hash") == request_hash:
                existing.metadata["cached"] = True
                logger.info(
                    "Returning cached scene analysis",
                    asset_id=asset_id,
                    project_id=project_id,
                    scenes=existing.scene_count,
                )
                return existing

        messages = build_scene_detection_messages(
            transcript,
            tone=tone,
            highlight_criteria=highlight_criteria,
            max_scenes=max_items,
            extra_instructions=extra_instructions,
        )

        try:
            response = await self.openai_client.chat_completion(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )
        except AIRetryableError:
            raise
        except AIMissingConfigurationError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            raise AIRetryableError(
                "Unexpected error during scene detection",
                context={"asset_id": asset_id},
            ) from exc

        content = self._extract_content(response)
        payload = self._parse_json_content(content, asset_id)

        scenes = self._build_scenes(
            payload.get("scenes") or [],
            asset_id=asset_id,
            project_id=project_id,
            request_id=request_hash,
        )

        run = SceneDetectionRun(
            id=str(uuid.uuid4()),
            asset_id=asset_id,
            project_id=project_id,
            tone=tone,
            criteria=highlight_criteria,
            max_scenes=max_items,
            source_model=self.model,
            parameters={
                "tone": tone,
                "criteria": highlight_criteria,
                "max_scenes": max_items,
                "extra_instructions": extra_instructions,
            },
            usage=response.get("usage", {}),
            generated_at=datetime.utcnow(),
            metadata={
                "request_hash": request_hash,
                "raw_metadata": payload.get("metadata", {}),
            },
            scenes=scenes,
        )

        saved = await self.scene_repository.save_run(run)
        logger.info(
            "Scene detection completed",
            asset_id=asset_id,
            project_id=project_id,
            scenes=saved.scene_count,
            cached=saved.metadata.get("cached", False),
            total_tokens=saved.usage.get("total_tokens"),
        )
        return saved

    def _extract_content(self, response: dict[str, Any]) -> str:
        choices = response.get("choices") or []
        if not choices:
            raise AIRetryableError("Scene analysis response did not include any choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "\n".join(part.get("text", "") for part in content if isinstance(part, dict))
        raise AIRetryableError("Unexpected scene analysis response format")

    def _parse_json_content(self, content: str, asset_id: str) -> dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            logger.error(
                "Failed to parse scene detection JSON",
                asset_id=asset_id,
                content_preview=content[:500],
                error=str(exc),
            )
            raise AIRetryableError("Scene analysis returned invalid JSON", context={"asset_id": asset_id}) from exc

    def _build_scenes(
        self,
        scenes_payload: list[dict[str, Any]],
        *,
        asset_id: str,
        project_id: str,
        request_id: str,
    ) -> list[SceneDetection]:
        scenes: list[SceneDetection] = []
        for index, item in enumerate(scenes_payload, start=1):
            try:
                start = float(item.get("start", 0.0))
                end = float(item.get("end", start))
            except (TypeError, ValueError):
                start, end = 0.0, 0.0
            if end < start:
                end = start
            confidence = item.get("confidence")
            try:
                confidence_value = float(confidence) if confidence is not None else None
            except (TypeError, ValueError):
                confidence_value = None
            tags = item.get("tags") or []
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
            tags = [str(tag).strip().lower() for tag in tags if str(tag).strip()]
            priority = item.get("priority")
            try:
                priority_value = int(priority) if priority is not None else index
            except (TypeError, ValueError):
                priority_value = index

            metadata: dict[str, Any] = {}
            if (recommended := item.get("recommended_duration")) is not None:
                metadata["recommended_duration"] = recommended

            scene = SceneDetection(
                id=str(uuid.uuid4()),
                asset_id=asset_id,
                project_id=project_id,
                title=str(item.get("title") or f"Scene {index}").strip(),
                description=str(item.get("description") or "").strip() or "AI generated highlight",
                start=start,
                end=end,
                confidence=confidence_value,
                priority=priority_value,
                tags=tags,
                request_id=request_id,
                metadata=metadata,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            scenes.append(scene)
        return scenes

    def _request_hash(self, *, tone: Optional[str], criteria: Optional[str], max_scenes: int) -> str:
        payload = f"{self.model}:{tone or ''}:{criteria or ''}:{max_scenes}"
        return uuid.uuid5(uuid.NAMESPACE_URL, payload).hex


__all__ = ["SceneAnalysisService"]
