from __future__ import annotations

import bisect
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from sqlalchemy import func, select

from ...models.clip import Clip, ClipVersion
from ...models.enums import ClipVersionStatus
from ...models.preset import Preset
from ...repositories.clip import ClipVersionRepository
from ..ai.analysis_service import SceneScore, TranscriptSegment
from .ffmpeg_service import SilenceSegment


class SplittingServiceError(RuntimeError):
    """Raised when the clip splitting workflow cannot be completed."""


@dataclass
class ClipPlanTarget:
    """Details of a requested clip planning target."""

    platform_key: str
    target_duration: float
    preset: Preset | None = None
    tolerance: float = 1.0
    max_segments: int = 3

    @property
    def preset_id(self) -> str | None:
        return self.preset.id if self.preset else None

    @property
    def resolved_platform_key(self) -> str:
        if self.platform_key:
            return self.platform_key
        return self.preset.key if self.preset else "default"


class ManualSegmentOverride(BaseModel):
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    label: str | None = None
    transition_out: str | None = None
    transition_out_duration: float | None = Field(default=None, ge=0)

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def _validate_order(self) -> "ManualSegmentOverride":
        if self.end <= self.start:
            raise ValueError("Override end time must be greater than start time")
        return self


class ClipPlanSegmentPayload(BaseModel):
    start: float
    end: float
    duration: float
    transcript_excerpt: str
    highlight_score: float
    scene_ids: list[str] = Field(default_factory=list)
    transition_in: str
    transition_in_duration: float | None = None
    transition_out: str
    transition_out_duration: float | None = None
    transition_out_locked: bool = False
    label: str | None = None
    is_manual: bool = False

    model_config = ConfigDict(validate_assignment=True)


class ClipPlanMetadataPayload(BaseModel):
    preset_id: str | None = None
    platform_key: str
    target_duration: float
    tolerance: float
    segments: list[ClipPlanSegmentPayload] = Field(default_factory=list)
    overrides_applied: list[str] = Field(default_factory=list)

    model_config = ConfigDict(validate_assignment=True)


@dataclass
class _SegmentDescriptor:
    start_index: int
    end_index: int
    is_manual: bool = False
    label: str | None = None
    transition_out_override: str | None = None
    transition_out_duration_override: float | None = None


@dataclass
class _SegmentContext:
    descriptor: _SegmentDescriptor
    raw_start: float
    raw_end: float
    segment: ClipPlanSegmentPayload


class SplittingService:
    """Creates platform-ready clip plans from transcript and scene metadata."""

    def __init__(
        self,
        clip_version_repository: ClipVersionRepository,
        *,
        default_tolerance: float = 1.0,
    ) -> None:
        self._clip_versions = clip_version_repository
        self._default_tolerance = default_tolerance

    # ------------------------------------------------------------------
    # Public API
    def generate_clip_plan(
        self,
        *,
        clip: Clip,
        targets: Sequence[ClipPlanTarget],
        transcript_segments: Sequence[TranscriptSegment | Mapping[str, Any]],
        scene_scores: Sequence[SceneScore | Mapping[str, Any]],
        silence_segments: Sequence[SilenceSegment | Mapping[str, Any]] | None = None,
        overrides: Sequence[ManualSegmentOverride | Mapping[str, Any]] | None = None,
    ) -> list[ClipVersion]:
        transcripts = self._normalise_transcripts(transcript_segments)
        if not transcripts:
            raise SplittingServiceError("Cannot generate clip plan without transcript segments")

        scenes = self._normalise_scene_scores(scene_scores)
        silences = self._normalise_silences(silence_segments or [])
        override_payloads = self._normalise_overrides(overrides or [])

        highlight_map = self._build_highlight_map(transcripts, scenes)
        versions: list[ClipVersion] = []

        base_version_number = self._next_version_number(clip.id) + 1
        for offset, target in enumerate(targets):
            tolerance = target.tolerance if target.tolerance > 0 else self._default_tolerance
            plan = self._build_plan_metadata(
                target=target,
                transcripts=transcripts,
                scenes=scenes,
                silences=silences,
                highlight_map=highlight_map,
                overrides=override_payloads,
                tolerance=tolerance,
            )
            version = self._clip_versions.create(
                {
                    "clip_id": clip.id,
                    "preset_id": target.preset_id,
                    "version_number": base_version_number + offset,
                    "status": ClipVersionStatus.DRAFT,
                    "plan_metadata": plan.model_dump(),
                }
            )
            versions.append(version)
        return versions

    def merge_segments(self, clip_version: ClipVersion, *, start_index: int) -> ClipVersion:
        if start_index < 0:
            raise IndexError("Segment index must be non-negative")
        metadata = clip_version.plan_metadata
        if not isinstance(metadata, dict):
            raise SplittingServiceError("Clip version does not contain a plan metadata payload")
        try:
            plan = ClipPlanMetadataPayload.model_validate(metadata)
        except ValidationError as exc:  # pragma: no cover - defensive guard
            raise SplittingServiceError("Stored plan metadata could not be parsed") from exc
        if start_index >= len(plan.segments) - 1:
            raise IndexError("Segment index must reference an adjacent pair")

        first = plan.segments[start_index]
        second = plan.segments[start_index + 1]
        merged = self._merge_segment_payloads(first, second)
        plan.segments[start_index] = merged
        del plan.segments[start_index + 1]
        self._recalculate_transitions(plan.segments, plan.tolerance)

        updated = self._clip_versions.update(
            clip_version,
            {"plan_metadata": plan.model_dump()},
        )
        return updated

    # ------------------------------------------------------------------
    # Internal helpers
    def _build_plan_metadata(
        self,
        *,
        target: ClipPlanTarget,
        transcripts: Sequence[TranscriptSegment],
        scenes: Sequence[SceneScore],
        silences: Sequence[SilenceSegment],
        highlight_map: Sequence[float],
        overrides: Sequence[ManualSegmentOverride],
        tolerance: float,
    ) -> ClipPlanMetadataPayload:
        descriptors = self._build_segment_descriptors(
            transcripts=transcripts,
            highlight_map=highlight_map,
            target_duration=target.target_duration,
            tolerance=tolerance,
            overrides=overrides,
            max_segments=max(target.max_segments, 1),
        )
        if not descriptors:
            descriptors = [
                _SegmentDescriptor(start_index=0, end_index=len(transcripts) - 1)
            ]

        contexts: list[_SegmentContext] = []
        for descriptor in descriptors:
            context = self._draft_segment(
                descriptor=descriptor,
                transcripts=transcripts,
                scenes=scenes,
                silences=silences,
                highlight_map=highlight_map,
                tolerance=tolerance,
            )
            contexts.append(context)

        contexts.sort(key=lambda ctx: ctx.segment.start)
        self._resolve_overlaps(contexts)
        segments = [ctx.segment for ctx in contexts]
        self._recalculate_transitions(segments, tolerance)

        overrides_applied = [
            descriptor.label
            for descriptor in descriptors
            if descriptor.is_manual and descriptor.label
        ]

        return ClipPlanMetadataPayload(
            preset_id=target.preset_id,
            platform_key=target.resolved_platform_key,
            target_duration=target.target_duration,
            tolerance=tolerance,
            segments=segments,
            overrides_applied=overrides_applied,
        )

    def _build_segment_descriptors(
        self,
        *,
        transcripts: Sequence[TranscriptSegment],
        highlight_map: Sequence[float],
        target_duration: float,
        tolerance: float,
        overrides: Sequence[ManualSegmentOverride],
        max_segments: int,
    ) -> list[_SegmentDescriptor]:
        if not transcripts:
            return []
        used_indices: set[int] = set()
        descriptors: list[_SegmentDescriptor] = []

        for override in sorted(overrides, key=lambda ov: ov.start):
            descriptor = self._descriptor_for_override(override, transcripts)
            if descriptor is None:
                continue
            descriptors.append(descriptor)
            used_indices.update(range(descriptor.start_index, descriptor.end_index + 1))

        available_indices = [idx for idx in range(len(transcripts)) if idx not in used_indices]
        while available_indices and len(descriptors) < max_segments:
            anchor = self._select_anchor(available_indices, highlight_map)
            descriptor = self._expand_descriptor(
                anchor_index=anchor,
                available_indices=available_indices,
                transcripts=transcripts,
                highlight_map=highlight_map,
                target_duration=target_duration,
                tolerance=tolerance,
            )
            descriptors.append(descriptor)
            used_indices.update(range(descriptor.start_index, descriptor.end_index + 1))
            available_indices = [idx for idx in available_indices if idx not in used_indices]

        if available_indices and descriptors:
            last = descriptors[-1]
            last.end_index = max(last.end_index, max(available_indices))
            used_indices.update(range(last.start_index, last.end_index + 1))
            available_indices = [idx for idx in available_indices if idx not in used_indices]

        if not descriptors and transcripts:
            descriptors.append(_SegmentDescriptor(start_index=0, end_index=len(transcripts) - 1))

        descriptors.sort(key=lambda descriptor: descriptor.start_index)
        return descriptors

    def _descriptor_for_override(
        self,
        override: ManualSegmentOverride,
        transcripts: Sequence[TranscriptSegment],
    ) -> _SegmentDescriptor | None:
        start_idx: int | None = None
        end_idx: int | None = None
        for idx, segment in enumerate(transcripts):
            if segment.end <= override.start:
                continue
            if start_idx is None:
                start_idx = idx
            if segment.start < override.end:
                end_idx = idx
            if segment.start >= override.end:
                break
        if start_idx is None or end_idx is None:
            return None
        return _SegmentDescriptor(
            start_index=start_idx,
            end_index=end_idx,
            is_manual=True,
            label=override.label,
            transition_out_override=override.transition_out,
            transition_out_duration_override=override.transition_out_duration,
        )

    def _select_anchor(self, candidates: Sequence[int], highlight_map: Sequence[float]) -> int:
        return max(candidates, key=lambda idx: (highlight_map[idx], -idx))

    def _expand_descriptor(
        self,
        *,
        anchor_index: int,
        available_indices: Sequence[int],
        transcripts: Sequence[TranscriptSegment],
        highlight_map: Sequence[float],
        target_duration: float,
        tolerance: float,
    ) -> _SegmentDescriptor:
        start_idx = anchor_index
        end_idx = anchor_index
        available = sorted(available_indices)

        def current_duration() -> float:
            return transcripts[end_idx].end - transcripts[start_idx].start

        while current_duration() < max(target_duration - tolerance, 0.0):
            prev_idx = self._previous_index(available, start_idx)
            next_idx = self._next_index(available, end_idx)
            candidates: list[tuple[str, int, float]] = []
            if prev_idx is not None:
                new_duration = transcripts[end_idx].end - transcripts[prev_idx].start
                candidates.append(("prev", prev_idx, abs(target_duration - new_duration)))
            if next_idx is not None:
                new_duration = transcripts[next_idx].end - transcripts[start_idx].start
                candidates.append(("next", next_idx, abs(target_duration - new_duration)))
            if not candidates:
                break
            candidates.sort(key=lambda item: (item[2], -highlight_map[item[1]]))
            direction, idx, _ = candidates[0]
            if direction == "prev":
                start_idx = idx
            else:
                end_idx = idx

        while current_duration() > target_duration + tolerance and end_idx > start_idx:
            shrink_options: list[tuple[int, int, float]] = []
            if start_idx < anchor_index:
                candidate_start = start_idx + 1
                if candidate_start <= anchor_index:
                    new_duration = transcripts[end_idx].end - transcripts[candidate_start].start
                    shrink_options.append((candidate_start, end_idx, abs(target_duration - new_duration)))
            if end_idx > anchor_index:
                candidate_end = end_idx - 1
                if candidate_end >= anchor_index:
                    new_duration = transcripts[candidate_end].end - transcripts[start_idx].start
                    shrink_options.append((start_idx, candidate_end, abs(target_duration - new_duration)))
            if not shrink_options:
                break
            shrink_options.sort(key=lambda item: item[2])
            start_idx, end_idx, _ = shrink_options[0]

        return _SegmentDescriptor(start_index=start_idx, end_index=end_idx)

    def _draft_segment(
        self,
        *,
        descriptor: _SegmentDescriptor,
        transcripts: Sequence[TranscriptSegment],
        scenes: Sequence[SceneScore],
        silences: Sequence[SilenceSegment],
        highlight_map: Sequence[float],
        tolerance: float,
    ) -> _SegmentContext:
        slice_transcripts = transcripts[descriptor.start_index : descriptor.end_index + 1]
        raw_start = slice_transcripts[0].start
        raw_end = slice_transcripts[-1].end

        start, end = self._align_boundaries(
            raw_start=raw_start,
            raw_end=raw_end,
            scenes=scenes,
            silences=silences,
            tolerance=tolerance,
        )
        if start < 0:
            start = 0.0
        if end <= start:
            end = raw_end
            start = raw_start

        excerpt = self._compose_excerpt(slice_transcripts)
        highlight_score = self._aggregate_highlight(highlight_map, descriptor.start_index, descriptor.end_index)
        scene_ids = sorted(
            {
                scene.scene_id
                for scene in scenes
                if scene.start < end and scene.end > start
            }
        )

        duration = max(end - start, raw_end - raw_start)
        segment = ClipPlanSegmentPayload(
            start=round(start, 3),
            end=round(end, 3),
            duration=round(duration, 3),
            transcript_excerpt=excerpt,
            highlight_score=round(highlight_score, 6),
            scene_ids=scene_ids,
            transition_in="cut",
            transition_in_duration=None,
            transition_out=descriptor.transition_out_override or "cut",
            transition_out_duration=descriptor.transition_out_duration_override,
            transition_out_locked=descriptor.transition_out_override is not None,
            label=descriptor.label,
            is_manual=descriptor.is_manual,
        )
        return _SegmentContext(descriptor=descriptor, raw_start=raw_start, raw_end=raw_end, segment=segment)

    def _resolve_overlaps(self, contexts: list[_SegmentContext]) -> None:
        for idx in range(1, len(contexts)):
            previous = contexts[idx - 1]
            current = contexts[idx]
            if current.segment.start < previous.segment.end:
                adjusted_start = max(current.raw_start, previous.segment.end)
                adjusted_start = round(adjusted_start, 3)
                if adjusted_start >= current.segment.end:
                    current.segment.end = round(current.raw_end, 3)
                current.segment.start = adjusted_start
                current.segment.duration = round(max(current.segment.end - current.segment.start, 0.1), 3)

    def _recalculate_transitions(self, segments: list[ClipPlanSegmentPayload], tolerance: float) -> None:
        for idx, segment in enumerate(segments):
            segment.duration = round(max(segment.end - segment.start, 0.0), 3)
            if idx == 0:
                segment.transition_in = "cut"
                segment.transition_in_duration = None
            else:
                previous = segments[idx - 1]
                gap = segment.start - previous.end
                if gap <= tolerance:
                    segment.transition_in = "crossfade"
                    segment.transition_in_duration = self._crossfade_duration(gap)
                else:
                    segment.transition_in = "cut"
                    segment.transition_in_duration = None

            if idx == len(segments) - 1:
                if segment.transition_out_locked:
                    if not segment.transition_out:
                        segment.transition_out = "cut"
                    continue
                segment.transition_out = "cut"
                segment.transition_out_duration = None
            else:
                if segment.transition_out_locked:
                    if segment.transition_out == "crossfade" and segment.transition_out_duration is None:
                        segment.transition_out_duration = self._crossfade_duration(tolerance / 2)
                    continue
                gap = segments[idx + 1].start - segment.end
                if gap <= tolerance:
                    segment.transition_out = "crossfade"
                    segment.transition_out_duration = self._crossfade_duration(gap)
                else:
                    segment.transition_out = "cut"
                    segment.transition_out_duration = None

    def _merge_segment_payloads(
        self,
        first: ClipPlanSegmentPayload,
        second: ClipPlanSegmentPayload,
    ) -> ClipPlanSegmentPayload:
        start = min(first.start, second.start)
        end = max(first.end, second.end)
        excerpt = self._merge_excerpts(first.transcript_excerpt, second.transcript_excerpt)
        scene_ids = sorted({*first.scene_ids, *second.scene_ids})
        highlight = max(first.highlight_score, second.highlight_score)
        return ClipPlanSegmentPayload(
            start=round(start, 3),
            end=round(end, 3),
            duration=round(max(end - start, 0.0), 3),
            transcript_excerpt=excerpt,
            highlight_score=round(highlight, 6),
            scene_ids=scene_ids,
            transition_in=first.transition_in,
            transition_in_duration=first.transition_in_duration,
            transition_out=second.transition_out,
            transition_out_duration=second.transition_out_duration,
            transition_out_locked=second.transition_out_locked,
            label=first.label or second.label,
            is_manual=first.is_manual or second.is_manual,
        )

    def _compose_excerpt(self, transcripts: Sequence[TranscriptSegment]) -> str:
        text = " ".join(segment.text.strip() for segment in transcripts if segment.text).strip()
        text = " ".join(text.split())
        if len(text) > 240:
            return text[:237] + "..."
        return text

    def _merge_excerpts(self, *excerpts: str) -> str:
        joined = " ".join(part.strip() for part in excerpts if part).strip()
        joined = " ".join(joined.split())
        if len(joined) > 240:
            return joined[:237] + "..."
        return joined

    def _aggregate_highlight(self, highlight_map: Sequence[float], start_idx: int, end_idx: int) -> float:
        values = highlight_map[start_idx : end_idx + 1]
        if not values:
            return 0.0
        return sum(values) / len(values)

    def _align_boundaries(
        self,
        *,
        raw_start: float,
        raw_end: float,
        scenes: Sequence[SceneScore],
        silences: Sequence[SilenceSegment],
        tolerance: float,
    ) -> tuple[float, float]:
        scene_starts = sorted(scene.start for scene in scenes)
        scene_ends = sorted(scene.end for scene in scenes)
        silence_starts = sorted(silence.start for silence in silences)
        silence_ends = sorted(silence.end for silence in silences)

        aligned_start = raw_start
        aligned_end = raw_end

        previous_scene_start = self._nearest_lte(scene_starts, raw_start)
        if previous_scene_start is not None and raw_start - previous_scene_start <= tolerance:
            aligned_start = previous_scene_start

        next_scene_end = self._nearest_gte(scene_ends, raw_end)
        if next_scene_end is not None and next_scene_end - raw_end <= tolerance:
            aligned_end = next_scene_end

        previous_silence_end = self._nearest_lte(silence_ends, aligned_start)
        if previous_silence_end is not None and aligned_start - previous_silence_end <= tolerance:
            aligned_start = previous_silence_end

        next_silence_start = self._nearest_gte(silence_starts, aligned_end)
        if next_silence_start is not None and next_silence_start - aligned_end <= tolerance:
            aligned_end = next_silence_start

        if aligned_end - aligned_start < 0.3:
            return raw_start, raw_end
        return aligned_start, aligned_end

    def _nearest_lte(self, values: Sequence[float], target: float) -> float | None:
        if not values:
            return None
        idx = bisect.bisect_right(values, target)
        if idx == 0:
            return None
        return values[idx - 1]

    def _nearest_gte(self, values: Sequence[float], target: float) -> float | None:
        if not values:
            return None
        idx = bisect.bisect_left(values, target)
        if idx >= len(values):
            return None
        return values[idx]

    def _crossfade_duration(self, gap: float) -> float:
        if gap <= 0:
            return 0.6
        return round(min(0.8, max(0.3, gap / 2)), 3)

    def _previous_index(self, values: Sequence[int], target: int) -> int | None:
        idx = bisect.bisect_left(values, target)
        if idx == 0:
            return None
        return values[idx - 1]

    def _next_index(self, values: Sequence[int], target: int) -> int | None:
        idx = bisect.bisect_right(values, target)
        if idx >= len(values):
            return None
        return values[idx]

    def _normalise_transcripts(
        self, segments: Sequence[TranscriptSegment | Mapping[str, Any]]
    ) -> list[TranscriptSegment]:
        normalised = [
            segment if isinstance(segment, TranscriptSegment) else TranscriptSegment.model_validate(segment)
            for segment in segments
        ]
        normalised.sort(key=lambda segment: segment.start)
        return normalised

    def _normalise_scene_scores(
        self, scene_scores: Sequence[SceneScore | Mapping[str, Any]]
    ) -> list[SceneScore]:
        normalised = [
            scene if isinstance(scene, SceneScore) else SceneScore.model_validate(scene)
            for scene in scene_scores
        ]
        normalised.sort(key=lambda scene: scene.start)
        return normalised

    def _normalise_silences(
        self, silences: Iterable[SilenceSegment | Mapping[str, Any]]
    ) -> list[SilenceSegment]:
        normalised: list[SilenceSegment] = []
        for silence in silences:
            if isinstance(silence, SilenceSegment):
                normalised.append(silence)
                continue
            payload = dict(silence)
            start = float(payload.get("start", 0.0))
            end = float(payload.get("end", start))
            duration = float(payload.get("duration", max(end - start, 0.0)))
            normalised.append(SilenceSegment(start=start, end=end, duration=duration))
        normalised.sort(key=lambda silence: silence.start)
        return normalised

    def _normalise_overrides(
        self, overrides: Sequence[ManualSegmentOverride | Mapping[str, Any]]
    ) -> list[ManualSegmentOverride]:
        return [
            override
            if isinstance(override, ManualSegmentOverride)
            else ManualSegmentOverride.model_validate(override)
            for override in overrides
        ]

    def _build_highlight_map(
        self,
        transcripts: Sequence[TranscriptSegment],
        scenes: Sequence[SceneScore],
    ) -> list[float]:
        if not transcripts:
            return []
        highlight_map: list[float] = []
        for segment in transcripts:
            overlaps = [
                scene.highlight_score
                for scene in scenes
                if scene.start < segment.end and scene.end > segment.start
            ]
            highlight_map.append(max(overlaps, default=0.0))
        return highlight_map

    def _next_version_number(self, clip_id: str) -> int:
        stmt = select(func.max(ClipVersion.version_number)).where(ClipVersion.clip_id == clip_id)
        result = self._clip_versions.session.execute(stmt).scalar()
        if result is None:
            return 0
        return int(result)


__all__ = [
    "ClipPlanMetadataPayload",
    "ClipPlanSegmentPayload",
    "ClipPlanTarget",
    "ManualSegmentOverride",
    "SplittingService",
]
