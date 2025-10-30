from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.main import create_app
from backend.app.models.base import Base
from backend.app.models.clip import Clip, ClipVersion
from backend.app.models.enums import ClipStatus, ClipVersionStatus, ProcessingJobStatus, ProcessingJobType, ProjectStatus
from backend.app.models.processing_job import ProcessingJob
from backend.app.models.project import Project


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


def test_create_project(client: TestClient) -> None:
    response = client.post(
        "/projects/",
        json={
            "name": "My Video Project",
            "description": "A test project",
            "status": "active",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Video Project"
    assert data["description"] == "A test project"
    assert data["status"] == "active"
    assert "id" in data
    assert "created_at" in data


def test_list_projects_empty(client: TestClient) -> None:
    response = client.get("/projects/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["offset"] == 0


def test_list_projects_with_data(client: TestClient, db_session: Session) -> None:
    for i in range(3):
        project = Project(
            id=f"proj-{i}",
            name=f"Project {i}",
            status=ProjectStatus.ACTIVE,
        )
        db_session.add(project)
    db_session.commit()
    
    response = client.get("/projects/")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert data["total"] == 3


def test_list_projects_pagination(client: TestClient, db_session: Session) -> None:
    for i in range(5):
        project = Project(
            id=f"proj-{i}",
            name=f"Project {i}",
            status=ProjectStatus.ACTIVE,
        )
        db_session.add(project)
    db_session.commit()
    
    response = client.get("/projects/?offset=2&limit=2")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["offset"] == 2
    assert data["limit"] == 2


def test_get_project(client: TestClient, db_session: Session) -> None:
    project = Project(
        id="test-proj",
        name="Test Project",
        description="Description",
        status=ProjectStatus.ACTIVE,
    )
    db_session.add(project)
    db_session.commit()
    
    response = client.get("/projects/test-proj")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-proj"
    assert data["name"] == "Test Project"
    assert data["description"] == "Description"


def test_get_project_not_found(client: TestClient) -> None:
    response = client.get("/projects/nonexistent")
    
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["message"].lower()


def test_update_project(client: TestClient, db_session: Session) -> None:
    project = Project(
        id="update-proj",
        name="Original Name",
        status=ProjectStatus.ACTIVE,
    )
    db_session.add(project)
    db_session.commit()
    
    response = client.put(
        "/projects/update-proj",
        json={"name": "Updated Name", "status": "archived"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["status"] == "archived"


def test_update_project_not_found(client: TestClient) -> None:
    response = client.put(
        "/projects/nonexistent",
        json={"name": "New Name"},
    )
    
    assert response.status_code == 404


def test_delete_project(client: TestClient, db_session: Session) -> None:
    project = Project(
        id="delete-proj",
        name="To Delete",
        status=ProjectStatus.ACTIVE,
    )
    db_session.add(project)
    db_session.commit()
    
    response = client.delete("/projects/delete-proj")
    
    assert response.status_code == 204
    
    get_response = client.get("/projects/delete-proj")
    assert get_response.status_code == 404


def test_delete_project_not_found(client: TestClient) -> None:
    response = client.delete("/projects/nonexistent")
    
    assert response.status_code == 404


def test_delete_project_with_active_jobs(client: TestClient, db_session: Session) -> None:
    project = Project(
        id="proj-with-jobs",
        name="Project",
        status=ProjectStatus.ACTIVE,
    )
    clip = Clip(
        id="clip-1",
        project_id=project.id,
        title="Clip",
        status=ClipStatus.DRAFT,
    )
    version = ClipVersion(
        id="version-1",
        clip_id="clip-1",
        version_number=1,
        status=ClipVersionStatus.DRAFT,
    )
    job = ProcessingJob(
        id="job-1",
        clip_version_id=version.id,
        job_type=ProcessingJobType.INGEST,
        status=ProcessingJobStatus.IN_PROGRESS,
        payload={},
    )
    
    db_session.add_all([project, clip, version, job])
    db_session.commit()
    
    response = client.delete("/projects/proj-with-jobs")
    
    assert response.status_code == 409
    data = response.json()
    assert "active processing job" in data["message"].lower()


def test_delete_project_with_completed_jobs(client: TestClient, db_session: Session) -> None:
    project = Project(
        id="proj-completed-jobs",
        name="Project",
        status=ProjectStatus.ACTIVE,
    )
    clip = Clip(
        id="clip-2",
        project_id=project.id,
        title="Clip",
        status=ClipStatus.DRAFT,
    )
    version = ClipVersion(
        id="version-2",
        clip_id="clip-2",
        version_number=1,
        status=ClipVersionStatus.DRAFT,
    )
    job = ProcessingJob(
        id="job-2",
        clip_version_id=version.id,
        job_type=ProcessingJobType.INGEST,
        status=ProcessingJobStatus.COMPLETED,
        payload={},
    )
    
    db_session.add_all([project, clip, version, job])
    db_session.commit()
    
    response = client.delete("/projects/proj-completed-jobs")
    
    assert response.status_code == 204
