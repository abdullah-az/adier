from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.main import create_app
from backend.app.models.base import Base
from backend.app.models.clip import Clip
from backend.app.models.project import Project
from backend.app.models.enums import ClipStatus, ProjectStatus


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    app = create_app()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    from backend.app.core.database import get_db
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_list_clips_empty(client: TestClient) -> None:
    response = client.get("/clips/")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_list_clips_with_project_filter(
    client: TestClient,
    db_session: Session,
) -> None:
    project_a = Project(id="proj-a", name="Project A", status=ProjectStatus.ACTIVE)
    project_b = Project(id="proj-b", name="Project B", status=ProjectStatus.ACTIVE)
    db_session.add_all([project_a, project_b])
    db_session.commit()

    for i in range(3):
        clip = Clip(
            id=f"clip-a-{i}",
            project_id=project_a.id,
            title=f"Clip A{i}",
            status=ClipStatus.DRAFT,
        )
        db_session.add(clip)

    clip_b = Clip(
        id="clip-b-1",
        project_id=project_b.id,
        title="Clip B1",
        status=ClipStatus.DRAFT,
    )
    db_session.add(clip_b)
    db_session.commit()

    response = client.get(f"/clips/?project_id={project_a.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


def test_get_clip_not_found(client: TestClient) -> None:
    response = client.get("/clips/nonexistent")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["message"].lower()


def test_get_clip(client: TestClient, db_session: Session) -> None:
    project = Project(id="proj", name="Project", status=ProjectStatus.ACTIVE)
    clip = Clip(
        id="clip-1",
        project_id=project.id,
        title="Test Clip",
        description="A test clip",
        status=ClipStatus.DRAFT,
    )
    db_session.add_all([project, clip])
    db_session.commit()

    response = client.get("/clips/clip-1")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "clip-1"
    assert data["title"] == "Test Clip"
    assert data["description"] == "A test clip"
