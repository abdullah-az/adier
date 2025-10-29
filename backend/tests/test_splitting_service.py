from __future__ import annotations

from pathlib import Path
from typing import Iterator, Sequence, Tuple

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.models.base import Base
from backend.app.models.clip import Clip
from backend.app.models.enums import PresetCategory
from backend.app.models.preset import Preset
from backend.app.models.project import Project
from backend.app.repositories.clip import ClipVersionRepository
from backend.app.services.ai.analysis_service import SceneScore, TranscriptSegment
from backend.app.services.video import (
    ClipPlanMetadataPayload,
    ClipPlanTarget,
    ManualSegmentOverride,
    SplittingService,
)
from backend.app.services.video.ffmpeg_service import SilenceSegment


@pytest.fixture()
def db_session(tmp_path: Path) -> Iterator[Session]:
    engine = create_engine(f"sqlite:///{tmp_path / 'splitting.db'}")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    try:
        with TestSession() as session:
            yield session
    finally:
        engine.dispose()


@pytest.fixture()
def clip_and_preset(db_session: Session) -> Tuple[Clip, Preset]:
    project = Project(name="Fitness Series")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    clip = Clip(project_id=project.id, title="Dynamic Warmup")
    preset = Preset(
        key="vertical_story",
        name="Vertical Story",
        category=PresetCategory.EXPORT,
        configuration={"target_duration": 10},
    )
    db_session.add_all([clip, preset])
    db_session.commit()
    db_session.refresh(clip)
    db_session.refresh(preset)
    return clip, preset


@pytest.fixture()
def sample_metadata() -> Tuple[Sequence[TranscriptSegment], Sequence[SceneScore], Sequence[SilenceSegment]]:
    transcripts = [
        TranscriptSegment(start=0.0, end=4.5, text="Intro to the workout."),
        TranscriptSegment(start=4.5, end=9.4, text="We begin with light cardio jumps."),
        TranscriptSegment(start=9.4, end=14.2, text="High intensity interval with explosive squats."),
        TranscriptSegment(start=14.2, end=18.9, text="Highlight moment with motivating shout-outs."),
        TranscriptSegment(start=18.9, end=24.7, text="Cool down and breathing guidance."),
    ]
    scenes = [
        SceneScore(
            scene_id="scene-1",
            start=0.0,
            end=6.0,
            semantic=0.4,
            sentiment=0.3,
            visual=0.2,
            highlight_score=0.55,
        ),
        SceneScore(
            scene_id="scene-2",
            start=6.0,
            end=14.8,
            semantic=0.8,
            sentiment=0.65,
            visual=0.85,
            highlight_score=0.92,
        ),
        SceneScore(
            scene_id="scene-3",
            start=14.8,
            end=24.8,
            semantic=0.6,
            sentiment=0.25,
            visual=0.5,
            highlight_score=0.7,
        ),
    ]
    silences = [
        SilenceSegment(start=5.7, end=6.2, duration=0.5),
        SilenceSegment(start=18.7, end=19.1, duration=0.4),
    ]
    return transcripts, scenes, silences


def test_generate_clip_plan_aligns_boundaries_and_persists_metadata(
    db_session: Session,
    clip_and_preset: Tuple[Clip, Preset],
    sample_metadata: Tuple[Sequence[TranscriptSegment], Sequence[SceneScore], Sequence[SilenceSegment]],
) -> None:
    clip, preset = clip_and_preset
    transcripts, scenes, silences = sample_metadata
    service = SplittingService(ClipVersionRepository(db_session))

    versions = service.generate_clip_plan(
        clip=clip,
        targets=[
            ClipPlanTarget(
                platform_key=preset.key,
                preset=preset,
                target_duration=10.0,
                tolerance=1.0,
                max_segments=3,
            )
        ],
        transcript_segments=transcripts,
        scene_scores=scenes,
        silence_segments=silences,
    )

    assert len(versions) == 1
    version = versions[0]
    assert version.clip_id == clip.id
    assert version.preset_id == preset.id
    assert version.plan_metadata is not None

    plan = ClipPlanMetadataPayload.model_validate(version.plan_metadata)
    assert plan.platform_key == preset.key
    assert len(plan.segments) >= 2

    first_segment = plan.segments[0]
    assert first_segment.start == pytest.approx(transcripts[0].start, abs=0.5)
    assert first_segment.end - first_segment.start == pytest.approx(10.0, abs=1.0)
    assert "Intro" in first_segment.transcript_excerpt
    assert first_segment.transition_out in {"cut", "crossfade"}

    for segment in plan.segments:
        assert segment.duration == pytest.approx(segment.end - segment.start, abs=1e-3)
        assert segment.highlight_score >= 0.0
        assert segment.transition_in in {"cut", "crossfade"}
        assert segment.transition_out in {"cut", "crossfade"}

    retrieved = ClipVersionRepository(db_session).get(version.id)
    assert retrieved is not None
    assert retrieved.plan_metadata == version.plan_metadata


def test_generate_clip_plan_respects_manual_override(
    db_session: Session,
    clip_and_preset: Tuple[Clip, Preset],
    sample_metadata: Tuple[Sequence[TranscriptSegment], Sequence[SceneScore], Sequence[SilenceSegment]],
) -> None:
    clip, preset = clip_and_preset
    transcripts, scenes, silences = sample_metadata
    service = SplittingService(ClipVersionRepository(db_session))

    overrides = [
        ManualSegmentOverride(
            start=9.0,
            end=18.5,
            label="Hero Moment",
            transition_out="crossfade",
            transition_out_duration=0.75,
        )
    ]

    version = service.generate_clip_plan(
        clip=clip,
        targets=[
            ClipPlanTarget(
                platform_key=preset.key,
                preset=preset,
                target_duration=10.0,
                tolerance=1.0,
            )
        ],
        transcript_segments=transcripts,
        scene_scores=scenes,
        silence_segments=silences,
        overrides=overrides,
    )[0]

    plan = ClipPlanMetadataPayload.model_validate(version.plan_metadata)
    manual_segments = [segment for segment in plan.segments if segment.is_manual]
    assert manual_segments, "Expected manual segment to be included in plan"
    manual = manual_segments[0]
    assert manual.label == "Hero Moment"
    assert manual.transition_out == "crossfade"
    assert manual.transition_out_duration == pytest.approx(0.75, rel=1e-2)
    assert manual.start == pytest.approx(transcripts[2].start, abs=0.6)
    assert plan.overrides_applied == ["Hero Moment"]


def test_merge_segments_reflows_transitions(
    db_session: Session,
    clip_and_preset: Tuple[Clip, Preset],
    sample_metadata: Tuple[Sequence[TranscriptSegment], Sequence[SceneScore], Sequence[SilenceSegment]],
) -> None:
    clip, preset = clip_and_preset
    transcripts, scenes, silences = sample_metadata
    repository = ClipVersionRepository(db_session)
    service = SplittingService(repository)

    target = ClipPlanTarget(
        platform_key=preset.key,
        preset=preset,
        target_duration=10.0,
        tolerance=1.0,
        max_segments=4,
    )
    version = service.generate_clip_plan(
        clip=clip,
        targets=[target],
        transcript_segments=transcripts,
        scene_scores=scenes,
        silence_segments=silences,
    )[0]
    original_plan = ClipPlanMetadataPayload.model_validate(version.plan_metadata)
    original_count = len(original_plan.segments)
    assert original_count >= 2

    updated = service.merge_segments(version, start_index=0)
    db_session.refresh(updated)

    merged_plan = ClipPlanMetadataPayload.model_validate(updated.plan_metadata)
    assert len(merged_plan.segments) == original_count - 1

    merged_first = merged_plan.segments[0]
    assert merged_first.duration > original_plan.segments[0].duration
    if len(merged_plan.segments) > 1:
        second = merged_plan.segments[1]
        assert second.transition_in in {"cut", "crossfade"}
        if second.transition_in == "crossfade":
            assert second.transition_in_duration is not None


pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
