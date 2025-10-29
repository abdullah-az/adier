from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from backend.app.models.media_asset import MediaAsset
from backend.app.repositories.media_asset import MediaAssetRepository
from backend.app.services.ai.providers import AllProvidersFailedError, ProviderErrorInfo
from backend.app.services.ai.router import AIProviderRouter

PROMPT_TEMPLATE = (
    "You are an expert video analyst helping editors understand the core story of a video.\n"
    "Review the transcript segments and the detected visual scenes. "
    "Identify the major topics, summarise the storyline, highlight the moments that would make great clips, "
    "and list notable people or entities.\n"
    "Return ONLY valid JSON that matches this schema:\n"
    "{\n"
    "  \"topics\": [\"<short topic>\", ...],\n"
    "  \"summary\": \"<concise summary paragraph>\",\n"
    "  \"entities\": [\n"
    "    {\n"
    "      \"name\": \"<entity or person>\",\n"
    "      \"type\": \"person|organization|location|other\",\n"
    "      \"mentions\": [\"<example mention>\", ...],\n"
    "      \"salience\": <number between 0 and 1>\n"
    "    }\n"
    "  ],\n"
    "  \"moments\": [\n"
    "    {\n"
    "      \"scene_id\": \"<scene identifier>\",\n"
    "      \"description\": \"<what happens>\",\n"
    "      \"reasons\": [\"<why it matters>\", ...]\n"
    "    }\n"
    "  ]\n"
    "}\n"
    "Transcript Segments:\n{transcript}\n\n"
    "Scene Breakdowns:\n{scenes}\n"
)


@dataclass(frozen=True)
class SceneScoringWeights:
    """Weights applied when combining scene-level signals into a highlight score."""

    semantic: float = 0.6
    sentiment: float = 0.25
    visual: float = 0.15

    def normalised(self) -> tuple[float, float, float]:
        components = [max(self.semantic, 0.0), max(self.sentiment, 0.0), max(self.visual, 0.0)]
        total = sum(components)
        if total <= 0:
            return (1.0, 0.0, 0.0)
        return tuple(component / total for component in components)


class TranscriptSegment(BaseModel):
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    text: str
    speaker: str | None = None

    model_config = ConfigDict(extra="ignore", frozen=True)


class SceneInput(BaseModel):
    scene_id: str
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    transcript: str
    sentiment: float | None = Field(default=None)
    visual_intensity: float | None = Field(default=None)
    tags: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore", frozen=True)


class ProviderEntity(BaseModel):
    name: str
    type: str = Field(default="other")
    mentions: list[str] = Field(default_factory=list)
    salience: float | None = Field(default=None)

    model_config = ConfigDict(extra="ignore")


class ProviderMoment(BaseModel):
    scene_id: str
    description: str
    reasons: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class ProviderAnalysisPayload(BaseModel):
    topics: list[str] = Field(default_factory=list)
    summary: str
    entities: list[ProviderEntity] = Field(default_factory=list)
    moments: list[ProviderMoment] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class EntityInfo(BaseModel):
    name: str
    type: str
    mentions: list[str] = Field(default_factory=list)
    salience: float | None = None

    model_config = ConfigDict(frozen=True)


class SceneScore(BaseModel):
    scene_id: str
    start: float
    end: float
    semantic: float
    sentiment: float
    visual: float
    highlight_score: float

    model_config = ConfigDict(frozen=True)


class KeyMoment(BaseModel):
    scene_id: str
    start: float
    end: float
    description: str
    highlight_score: float
    reasons: list[str] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True)


class VideoAnalysisResult(BaseModel):
    topics: list[str]
    summary: str
    entities: list[EntityInfo]
    key_moments: list[KeyMoment]
    scene_scores: list[SceneScore]

    model_config = ConfigDict(frozen=True)


class AnalysisServiceError(Exception):
    def __init__(self, message: str, *, retryable: bool, details: Dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.details = details or {}


class AnalysisService:
    """High-level orchestration for video understanding using LLM providers."""

    def __init__(
        self,
        router: AIProviderRouter,
        repository: MediaAssetRepository,
        *,
        weights: SceneScoringWeights | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._router = router
        self._repository = repository
        self._weights = weights or SceneScoringWeights()
        self._logger = logger or logging.getLogger("backend.app.services.ai.analysis")

    def analyse_media_asset(
        self,
        *,
        asset: MediaAsset,
        transcript_segments: Sequence[TranscriptSegment | Mapping[str, Any]],
        scenes: Sequence[SceneInput | Mapping[str, Any]],
        refresh: bool = False,
    ) -> VideoAnalysisResult:
        validated_segments = self._normalise_segments(transcript_segments)
        validated_scenes = self._normalise_scenes(scenes)
        cache_key = self._generate_cache_key(validated_segments, validated_scenes)

        if not refresh:
            cached = self._load_from_cache(asset, cache_key)
            if cached is not None:
                self._logger.debug("Returning cached analysis", extra={"extra": {"asset_id": asset.id}})
                return cached

        prompt = self._build_prompt(validated_segments, validated_scenes)

        try:
            response = self._router.generate_text(prompt=prompt)
        except AllProvidersFailedError as exc:  # pragma: no cover - error path validated via tests
            retryable = any(error.retryable for error in exc.errors)
            detail_payload = {
                "errors": [self._error_info_to_dict(error) for error in exc.errors],
                "asset_id": asset.id,
            }
            message = "All AI providers failed: " + "; ".join(f"{error.provider}: {error.message}" for error in exc.errors)
            raise AnalysisServiceError(message, retryable=retryable, details=detail_payload) from exc
        except Exception as exc:  # pragma: no cover - defensive logging for unexpected errors
            self._logger.exception("Unexpected error calling AI provider", exc_info=exc)
            raise AnalysisServiceError("AI provider request failed", retryable=True) from exc

        payload = self._parse_provider_payload(response.content)

        scene_scores = self._compute_scene_scores(validated_scenes, payload.topics)
        scene_lookup = {scene.scene_id: scene for scene in validated_scenes}
        score_lookup = {score.scene_id: score for score in scene_scores}
        key_moments = self._build_key_moments(payload.moments, scene_lookup, score_lookup)
        entities = [
            EntityInfo(name=entity.name, type=entity.type, mentions=entity.mentions, salience=entity.salience)
            for entity in payload.entities
        ]

        result = VideoAnalysisResult(
            topics=payload.topics,
            summary=payload.summary,
            entities=entities,
            key_moments=key_moments,
            scene_scores=scene_scores,
        )

        cache_payload = result.model_dump()
        self._repository.update_analysis_cache(asset, cache_key=cache_key, result=cache_payload)
        return result

    def _normalise_segments(
        self, segments: Sequence[TranscriptSegment | Mapping[str, Any]]
    ) -> list[TranscriptSegment]:
        return [
            segment if isinstance(segment, TranscriptSegment) else TranscriptSegment.model_validate(segment)
            for segment in segments
        ]

    def _normalise_scenes(self, scenes: Sequence[SceneInput | Mapping[str, Any]]) -> list[SceneInput]:
        return [scene if isinstance(scene, SceneInput) else SceneInput.model_validate(scene) for scene in scenes]

    def _load_from_cache(self, asset: MediaAsset, cache_key: str) -> VideoAnalysisResult | None:
        cache = asset.analysis_cache
        if not isinstance(cache, dict):
            return None
        if cache.get("hash") != cache_key:
            return None
        result_payload = cache.get("result")
        if not isinstance(result_payload, dict):
            return None
        try:
            cached = VideoAnalysisResult.model_validate(result_payload)
        except ValidationError:
            self._logger.warning(
                "Cached analysis could not be validated; regenerating",
                extra={"extra": {"asset_id": asset.id}},
            )
            return None
        return cached

    def _build_prompt(self, segments: Sequence[TranscriptSegment], scenes: Sequence[SceneInput]) -> str:
        transcript_block = self._format_transcript(segments)
        scenes_block = self._format_scenes(scenes)
        return PROMPT_TEMPLATE.format(transcript=transcript_block, scenes=scenes_block)

    def _format_transcript(self, segments: Sequence[TranscriptSegment]) -> str:
        lines: list[str] = []
        for index, segment in enumerate(segments, start=1):
            speaker = f"{segment.speaker}: " if segment.speaker else ""
            lines.append(
                f"{index}. {segment.start:.2f}s–{segment.end:.2f}s | {speaker}{segment.text.strip()}"
            )
        return "\n".join(lines) if lines else "(no transcript segments)"

    def _format_scenes(self, scenes: Sequence[SceneInput]) -> str:
        lines: list[str] = []
        for index, scene in enumerate(scenes, start=1):
            sentiment = (
                f"sentiment={scene.sentiment:+.2f}" if scene.sentiment is not None else "sentiment=neutral"
            )
            visual = (
                f"visual={scene.visual_intensity:.2f}" if scene.visual_intensity is not None else "visual=neutral"
            )
            tags = f"tags={', '.join(scene.tags)}" if scene.tags else "tags=none"
            transcript_excerpt = scene.transcript.replace("\n", " ").strip()
            if len(transcript_excerpt) > 160:
                transcript_excerpt = transcript_excerpt[:157] + "..."
            lines.append(
                f"{index}. Scene {scene.scene_id} [{scene.start:.2f}-{scene.end:.2f}s] ({sentiment}, {visual}, {tags}) -> {transcript_excerpt}"
            )
        return "\n".join(lines) if lines else "(no scene data)"

    def _parse_provider_payload(self, content: str) -> ProviderAnalysisPayload:
        payload_text = self._strip_code_fence(content.strip())
        try:
            raw = json.loads(payload_text)
        except json.JSONDecodeError as exc:
            raise AnalysisServiceError(
                "AI provider returned invalid JSON payload",
                retryable=False,
                details={"error": str(exc)},
            ) from exc
        try:
            return ProviderAnalysisPayload.model_validate(raw)
        except ValidationError as exc:
            raise AnalysisServiceError(
                "AI provider response did not match expected schema",
                retryable=False,
                details={"errors": exc.errors()},
            ) from exc

    def _strip_code_fence(self, value: str) -> str:
        stripped = value.strip()
        if not stripped.startswith("```"):
            return stripped
        lines = stripped.splitlines()
        if not lines:
            return stripped
        opener = lines.pop(0).strip()
        if opener.startswith("```") and len(opener) > 3:
            # Handles ```json, ```JSON etc. by simply discarding the opener line
            pass
        if lines and lines[0].strip().lower().startswith("json"):
            lines.pop(0)
        while lines and lines[-1].strip() == "```":
            lines.pop()
        return "\n".join(lines).strip()

    def _compute_scene_scores(self, scenes: Sequence[SceneInput], topics: Sequence[str]) -> list[SceneScore]:
        semantic_weight, sentiment_weight, visual_weight = self._weights.normalised()
        scores: list[SceneScore] = []
        for scene in scenes:
            semantic_score = self._semantic_score(scene, topics)
            sentiment_score = self._normalise_sentiment(scene.sentiment)
            visual_score = self._normalise_visual(scene.visual_intensity)
            highlight = (
                semantic_score * semantic_weight
                + sentiment_score * sentiment_weight
                + visual_score * visual_weight
            )
            scores.append(
                SceneScore(
                    scene_id=scene.scene_id,
                    start=scene.start,
                    end=scene.end,
                    semantic=semantic_score,
                    sentiment=sentiment_score,
                    visual=visual_score,
                    highlight_score=highlight,
                )
            )
        scores.sort(key=lambda s: s.start)
        return scores

    def _semantic_score(self, scene: SceneInput, topics: Sequence[str]) -> float:
        if not topics:
            return 0.0
        transcript_lower = scene.transcript.lower()
        tags_lower = [tag.lower() for tag in scene.tags]
        matches = 0
        for topic in topics:
            topic_lower = topic.lower()
            if topic_lower in transcript_lower or any(topic_lower in tag for tag in tags_lower):
                matches += 1
        return min(1.0, matches / max(len(topics), 1))

    def _normalise_sentiment(self, sentiment: float | None) -> float:
        if sentiment is None:
            return 0.5
        clamped = max(min(sentiment, 1.0), -1.0)
        return (clamped + 1.0) / 2.0

    def _normalise_visual(self, visual: float | None) -> float:
        if visual is None:
            return 0.5
        return max(0.0, min(visual, 1.0))

    def _build_key_moments(
        self,
        moments: Sequence[ProviderMoment],
        scene_lookup: Dict[str, SceneInput],
        score_lookup: Dict[str, SceneScore],
    ) -> list[KeyMoment]:
        compiled: list[KeyMoment] = []
        for moment in moments:
            scene = scene_lookup.get(moment.scene_id)
            score = score_lookup.get(moment.scene_id)
            if scene is None or score is None:
                continue
            compiled.append(
                KeyMoment(
                    scene_id=scene.scene_id,
                    start=scene.start,
                    end=scene.end,
                    description=moment.description,
                    highlight_score=score.highlight_score,
                    reasons=moment.reasons or [],
                )
            )
        if not compiled and score_lookup:
            top_scene = max(score_lookup.values(), key=lambda s: s.highlight_score)
            scene = scene_lookup[top_scene.scene_id]
            compiled.append(
                KeyMoment(
                    scene_id=scene.scene_id,
                    start=scene.start,
                    end=scene.end,
                    description=f"Scene from {scene.start:.2f}s to {scene.end:.2f}s",
                    highlight_score=top_scene.highlight_score,
                    reasons=["Automatically selected based on highlight scoring."],
                )
            )
        compiled.sort(key=lambda item: (item.start, -item.highlight_score))
        return compiled

    def _error_info_to_dict(self, info: ProviderErrorInfo) -> dict[str, Any]:
        return {
            "provider": info.provider,
            "message": info.message,
            "code": info.code,
            "status_code": info.status_code,
            "retryable": info.retryable,
            "extra": info.extra,
        }

    def _generate_cache_key(
        self,
        segments: Sequence[TranscriptSegment],
        scenes: Sequence[SceneInput],
    ) -> str:
        payload = {
            "transcript": [segment.model_dump() for segment in segments],
            "scenes": [scene.model_dump() for scene in scenes],
            "weights": asdict(self._weights),
        }
        serialised = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialised.encode("utf-8")).hexdigest()


__all__ = [
    "AnalysisService",
    "AnalysisServiceError",
    "SceneInput",
    "SceneScore",
    "SceneScoringWeights",
    "TranscriptSegment",
    "VideoAnalysisResult",
    "KeyMoment",
    "EntityInfo",
]
