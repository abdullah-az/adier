from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from loguru import logger

from app.core.config import Settings
from app.models.scene import SceneAnalysis, SceneDetection
from app.models.transcription import Transcript
from app.repositories.scene_repository import SceneAnalysisRepository
from app.repositories.transcript_repository import TranscriptRepository
from app.repositories.video_repository import VideoAssetRepository
from app.services.openai_service import OpenAIConfigurationError, OpenAIService
from app.services.prompt_service import PromptService
from app.services.job_service import JobExecutionContext


class SceneDetectionService:
    """Run AI-powered scene detection using transcripts and OpenAI."""

    def __init__(
        self,
        *,
        settings: Settings,
        video_repository: VideoAssetRepository,
        transcript_repository: TranscriptRepository,
        scene_repository: SceneAnalysisRepository,
        prompt_service: PromptService,
        openai_service: OpenAIService,
    ) -> None:
        self.settings = settings
        self.video_repository = video_repository
        self.transcript_repository = transcript_repository
        self.scene_repository = scene_repository
        self.prompt_service = prompt_service
        self.openai_service = openai_service

        self.scene_model = getattr(settings, "openai_scene_model", "gpt-4o-mini")
        self.scene_temperature = float(getattr(settings, "scene_detection_temperature", 0.2))
        self.scene_max_scenes = int(getattr(settings, "scene_detection_max_scenes", 5))
        self.scene_transcript_char_limit = int(getattr(settings, "scene_detection_transcript_char_limit", 12000))
        self.scene_min_confidence = float(getattr(settings, "scene_detection_min_confidence", 0.3))

    async def run_scene_detection_job(self, context: JobExecutionContext) -> Dict[str, Any]:
        payload = context.payload
        asset_id = payload.get("asset_id")
        if not asset_id:
            raise ValueError("Scene detection job payload missing 'asset_id'")

        force = bool(payload.get("force", False))
        keep_history = bool(payload.get("keep_history", False))
        max_scenes = payload.get("max_scenes") or self.scene_max_scenes
        tone_override = payload.get("tone")
        criteria_override = payload.get("highlight_criteria")
        prompt_overrides: Dict[str, Any] = payload.get("prompt_overrides") or {}
        prompt_overrides.setdefault("max_scenes", max_scenes)
        if tone_override:
            prompt_overrides["tone"] = tone_override
        if criteria_override:
            prompt_overrides["highlight_criteria"] = criteria_override

        await context.progress(5.0, message="Loading asset metadata")
        asset = await self.video_repository.get(asset_id)
        if asset is None or asset.project_id != context.project_id:
            raise ValueError("Video asset not found for scene detection")

        existing_analysis = await self.scene_repository.get_latest_for_asset(asset_id)
        if existing_analysis and not force:
            await context.log(
                "Scene detection already exists; skipping (use force=true to regenerate)",
                analysis_id=existing_analysis.id,
            )
            await context.progress(100.0, message="Scene analysis already available")
            return {
                "asset_id": asset_id,
                "analysis_id": existing_analysis.id,
                "scene_count": len(existing_analysis.scenes),
                "cached": True,
            }

        await context.progress(10.0, message="Fetching transcript")
        transcript = await self.transcript_repository.get_by_asset(asset_id)
        if transcript is None:
            raise RuntimeError("Transcript required for scene detection is missing")

        excerpt = self._build_transcript_excerpt(transcript, limit=self.scene_transcript_char_limit)
        await context.log("Prepared transcript excerpt", length=len(excerpt))

        system_prompt, user_prompt, prompt_metadata = self.prompt_service.build_scene_detection_prompt(
            excerpt,
            overrides=prompt_overrides,
        )

        await context.progress(25.0, message="Requesting scene analysis from OpenAI")
        try:
            result, usage = await self.openai_service.generate_json_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=self.scene_model,
                temperature=self.scene_temperature,
            )
        except OpenAIConfigurationError as exc:
            raise RuntimeError("OpenAI configuration is required for scene detection") from exc
        except Exception as exc:  # pragma: no cover - depends on API behaviour
            raise RuntimeError(f"OpenAI scene detection failed: {exc}") from exc

        scenes_payload = result.get("scenes") or []
        if not scenes_payload:
            raise RuntimeError("Scene detection returned no scenes; please adjust prompt criteria")

        scenes = self._parse_scenes(
            scenes_payload,
            transcript=transcript,
        )
        scenes.sort(key=lambda item: item.start_seconds)

        analysis = SceneAnalysis(
            id=str(uuid4()),
            project_id=asset.project_id,
            asset_id=asset.id,
            model=self.scene_model,
            summary=result.get("summary"),
            scenes=scenes,
            usage=usage,
            prompt=prompt_metadata,
            metadata={
                "raw_result": result,
                "generated_at": datetime.utcnow().isoformat(),
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        await self.scene_repository.save(analysis, replace_existing=not keep_history)

        asset.metadata.setdefault("analysis", {})["scene_detection"] = {
            "analysis_id": analysis.id,
            "scene_count": len(scenes),
            "generated_at": analysis.created_at.isoformat(),
        }
        asset.updated_at = datetime.utcnow()
        await self.video_repository.update(asset)

        await context.progress(100.0, message="Scene analysis stored", analysis_id=analysis.id)
        await context.log(
            "Scene detection completed",
            analysis_id=analysis.id,
            scene_count=len(scenes),
            usage=usage,
        )

        return {
            "asset_id": asset.id,
            "analysis_id": analysis.id,
            "scene_count": len(scenes),
            "usage": usage,
            "summary": analysis.summary,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _build_transcript_excerpt(self, transcript: Transcript, *, limit: int) -> str:
        lines = [
            f"[{segment.start_timecode} - {segment.end_timecode}] {segment.text.strip()}"
            for segment in transcript.segments
        ]
        excerpt = []
        current_length = 0
        for line in lines:
            if current_length + len(line) + 1 > limit:
                break
            excerpt.append(line)
            current_length += len(line) + 1
        if not excerpt:
            excerpt = lines[: limit // 80 + 1]
        if len(excerpt) < len(lines):
            excerpt.append("...")
        return "\n".join(excerpt)

    def _parse_scenes(self, scenes_payload: List[Dict[str, Any]], *, transcript: Transcript) -> List[SceneDetection]:
        parsed: List[SceneDetection] = []
        for idx, scene in enumerate(scenes_payload):
            start_seconds = self._parse_time(scene, "start_seconds", fallback_keys=("start", "start_time"))
            end_seconds = self._parse_time(scene, "end_seconds", fallback_keys=("end", "end_time"))
            if end_seconds < start_seconds:
                end_seconds = start_seconds

            highlight_score = self._clamp_float(scene.get("highlight_score"), default=0.5)
            confidence = self._clamp_float(scene.get("confidence"), default=highlight_score)
            if confidence < self.scene_min_confidence:
                confidence = max(self.scene_min_confidence, confidence)

            tags = scene.get("tags") or []
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(",") if tag.strip()]

            recommended_duration = scene.get("recommended_duration")
            if recommended_duration is None:
                recommended_duration = max(0.0, round(end_seconds - start_seconds, 2))

            parsed.append(
                SceneDetection(
                    id=str(uuid4()),
                    index=scene.get("index", idx),
                    title=scene.get("title") or f"Scene {idx + 1}",
                    description=scene.get("description") or "",
                    start_seconds=round(start_seconds, 3),
                    end_seconds=round(end_seconds, 3),
                    start_timecode=self._format_timecode(start_seconds),
                    end_timecode=self._format_timecode(end_seconds),
                    highlight_score=self._clamp_float(highlight_score),
                    confidence=self._clamp_float(confidence),
                    tags=list(tags),
                    recommended_duration=self._clamp_float(recommended_duration, minimum=0.0, maximum=float("inf")),
                    metadata={
                        "source_index": scene.get("index", idx),
                        "raw": scene,
                    },
                )
            )
        return parsed

    def _parse_time(self, payload: Dict[str, Any], key: str, fallback_keys: tuple[str, ...]) -> float:
        value = payload.get(key)
        if value is None:
            for fallback in fallback_keys:
                value = payload.get(fallback)
                if value is not None:
                    break
        if isinstance(value, str) and ":" in value:
            return self._timecode_to_seconds(value)
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _clamp_float(self, value: Any, *, default: float = 0.0, minimum: float = 0.0, maximum: float = 1.0) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = default
        return max(minimum, min(maximum, numeric))

    def _format_timecode(self, seconds: float) -> str:
        total_milliseconds = int(round(seconds * 1000))
        hours, remainder = divmod(total_milliseconds, 3600_000)
        minutes, remainder = divmod(remainder, 60_000)
        secs, millis = divmod(remainder, 1000)
        return f"{hours:02}:{minutes:02}:{secs:02}.{millis:03}"

    def _timecode_to_seconds(self, timecode: str) -> float:
        try:
            part = timecode.strip()
            if "," in part:
                part = part.replace(",", ".")
            hours, minutes, rest = part.split(":")
            seconds = float(rest)
            total = int(hours) * 3600 + int(minutes) * 60 + seconds
            return float(total)
        except Exception:  # pragma: no cover - defensive parsing
            return 0.0
