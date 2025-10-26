from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path

import pytest

from app.models.scene_detection import SceneDetection, SceneDetectionRun
from app.models.subtitle import SubtitleSegment, SubtitleTranscript
from app.repositories.scene_repository import SceneDetectionRepository
from app.repositories.subtitle_repository import SubtitleRepository


@pytest.mark.asyncio
async def test_subtitle_repository_roundtrip(tmp_path: Path) -> None:
    repository = SubtitleRepository(tmp_path)
    transcript = SubtitleTranscript(
        id="request-1",
        asset_id="asset-123",
        project_id="project-1",
        language="en",
        text="Hello world",
        segments=[
            SubtitleSegment(
                id="seg-1",
                asset_id="asset-123",
                project_id="project-1",
                index=0,
                start=0.0,
                end=2.5,
                text="Hello",
                confidence=0.95,
                language="en",
                speaker="A",
                request_id="request-1",
            ),
            SubtitleSegment(
                id="seg-2",
                asset_id="asset-123",
                project_id="project-1",
                index=1,
                start=2.5,
                end=4.0,
                text="world",
                confidence=0.9,
                language="en",
                speaker="A",
                request_id="request-1",
            ),
        ],
        usage={"total_tokens": 100},
        metadata={"request_hash": "hash"},
    )

    await repository.save_transcript(transcript)

    stored = await repository.get_transcript("asset-123")
    assert stored is not None
    assert stored.asset_id == transcript.asset_id
    assert stored.segment_count == 2
    assert stored.duration == pytest.approx(4.0)
    assert stored.segments[0].text == "Hello"

    transcripts = await repository.list_project_transcripts("project-1")
    assert len(transcripts) == 1
    assert transcripts[0].asset_id == "asset-123"


@pytest.mark.asyncio
async def test_scene_repository_latest(tmp_path: Path) -> None:
    repository = SceneDetectionRepository(tmp_path)

    first_run = SceneDetectionRun(
        id="run-1",
        asset_id="asset-abc",
        project_id="project-1",
        generated_at=datetime.utcnow(),
        scenes=[
            SceneDetection(
                id="scene-1",
                asset_id="asset-abc",
                project_id="project-1",
                title="Intro",
                description="Opening scene",
                start=0.0,
                end=10.0,
                confidence=0.8,
                priority=1,
                tags=["intro"],
                request_id="req-1",
            )
        ],
        metadata={"request_hash": "hash-1"},
    )

    second_run = SceneDetectionRun(
        id="run-2",
        asset_id="asset-abc",
        project_id="project-1",
        generated_at=datetime.utcnow(),
        scenes=[
            SceneDetection(
                id="scene-2",
                asset_id="asset-abc",
                project_id="project-1",
                title="Hook",
                description="Key moment",
                start=12.0,
                end=25.0,
                confidence=0.9,
                priority=1,
                tags=["hook"],
                request_id="req-2",
            )
        ],
        metadata={"request_hash": "hash-2"},
    )

    await repository.save_run(first_run)
    await asyncio.sleep(0.01)
    await repository.save_run(second_run)

    latest = await repository.get_latest("asset-abc")
    assert latest is not None
    assert latest.id == "run-2"
    assert latest.scene_count == 1
    runs = await repository.list_runs("asset-abc")
    assert len(runs) == 2
