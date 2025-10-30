from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.models.base import Base
from backend.app.models.clip import Clip, ClipVersion
from backend.app.models.enums import ClipStatus, ClipVersionStatus
from backend.app.models.project import Project
from backend.app.models.enums import ProjectStatus
from backend.app.repositories.clip import ClipVersionRepository


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


@pytest.fixture()
def repository(db_session: Session) -> ClipVersionRepository:
    return ClipVersionRepository(db_session)


@pytest.fixture()
def sample_project(db_session: Session) -> Project:
    project = Project(
        id="project-1",
        name="Test Project",
        status=ProjectStatus.ACTIVE,
    )
    db_session.add(project)
    db_session.commit()
    return project


@pytest.fixture()
def sample_clip(db_session: Session, sample_project: Project) -> Clip:
    clip = Clip(
        id="clip-1",
        project_id=sample_project.id,
        title="Test Clip",
        status=ClipStatus.DRAFT,
    )
    db_session.add(clip)
    db_session.commit()
    return clip


def test_update_quality_metrics(
    repository: ClipVersionRepository,
    db_session: Session,
    sample_clip: Clip,
) -> None:
    version = ClipVersion(
        id="version-1",
        clip_id=sample_clip.id,
        version_number=1,
        status=ClipVersionStatus.DRAFT,
    )
    db_session.add(version)
    db_session.commit()

    metrics = {
        "sharpness": 0.8,
        "exposure": 0.7,
        "motion_blur": 0.2,
        "noise_level": 0.9,
        "audio_quality": 0.85,
        "overall_score": 0.8,
    }

    updated = repository.update_quality_metrics(version, metrics)

    assert updated.quality_metrics is not None
    assert updated.quality_metrics["sharpness"] == 0.8
    assert updated.quality_metrics["overall_score"] == 0.8


def test_get_versions_by_quality_threshold(
    repository: ClipVersionRepository,
    db_session: Session,
    sample_project: Project,
    sample_clip: Clip,
) -> None:
    versions = []
    for i in range(5):
        clip = Clip(
            id=f"clip-threshold-{i}",
            project_id=sample_project.id,
            title=f"Clip {i}",
            status=ClipStatus.DRAFT,
        )
        db_session.add(clip)
        db_session.commit()

        version = ClipVersion(
            id=f"version-threshold-{i}",
            clip_id=clip.id,
            version_number=1,
            status=ClipVersionStatus.DRAFT,
            quality_metrics={
                "overall_score": 0.4 + (i * 0.1),
            },
        )
        db_session.add(version)
        versions.append(version)

    db_session.commit()

    high_quality = repository.get_versions_by_quality_threshold(sample_project.id, 0.65)

    assert len(high_quality) == 2


def test_quality_metrics_persisted_correctly(
    repository: ClipVersionRepository,
    db_session: Session,
    sample_clip: Clip,
) -> None:
    version = ClipVersion(
        id="version-persist",
        clip_id=sample_clip.id,
        version_number=1,
        status=ClipVersionStatus.DRAFT,
    )
    db_session.add(version)
    db_session.commit()

    metrics = {
        "sharpness": 0.95,
        "exposure": 0.88,
        "motion_blur": 0.15,
        "noise_level": 0.92,
        "audio_quality": 0.91,
        "overall_score": 0.93,
    }

    repository.update_quality_metrics(version, metrics)

    retrieved = repository.get(version.id)
    assert retrieved is not None
    assert retrieved.quality_metrics is not None
    assert retrieved.quality_metrics["sharpness"] == pytest.approx(0.95)
    assert retrieved.quality_metrics["overall_score"] == pytest.approx(0.93)


def test_update_quality_metrics_overwrites_existing(
    repository: ClipVersionRepository,
    db_session: Session,
    sample_clip: Clip,
) -> None:
    version = ClipVersion(
        id="version-overwrite",
        clip_id=sample_clip.id,
        version_number=1,
        status=ClipVersionStatus.DRAFT,
        quality_metrics={"overall_score": 0.5},
    )
    db_session.add(version)
    db_session.commit()

    new_metrics = {
        "sharpness": 0.9,
        "overall_score": 0.9,
    }

    updated = repository.update_quality_metrics(version, new_metrics)

    assert updated.quality_metrics["overall_score"] == 0.9
    assert updated.quality_metrics["sharpness"] == 0.9
