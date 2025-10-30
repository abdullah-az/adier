from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.main import create_app
from backend.app.models.base import Base
from backend.app.models.enums import PresetCategory
from backend.app.models.preset import Preset


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


def test_list_presets_empty(client: TestClient) -> None:
    response = client.get("/presets/")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_list_presets_with_category(
    client: TestClient,
    db_session: Session,
) -> None:
    presets = [
        Preset(
            id=f"preset-{i}",
            key=f"preset_{i}",
            name=f"Preset {i}",
            category=PresetCategory.EXPORT,
            configuration={"resolution": "1080p"},
        )
        for i in range(3)
    ]
    presets.append(
        Preset(
            id="preset-audio",
            key="audio",
            name="Audio Preset",
            category=PresetCategory.AUDIO,
            configuration={"eq": "flat"},
        )
    )
    db_session.add_all(presets)
    db_session.commit()

    response = client.get("/presets/?category=export")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert all(item["category"] == PresetCategory.EXPORT.value for item in data["items"])


def test_get_preset_not_found(client: TestClient) -> None:
    response = client.get("/presets/missing")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["message"].lower()


def test_get_preset(client: TestClient, db_session: Session) -> None:
    preset = Preset(
        id="preset-1",
        key="preset",
        name="Preset",
        category=PresetCategory.EXPORT,
        configuration={"format": "mp4"},
        description="Export preset",
    )
    db_session.add(preset)
    db_session.commit()

    response = client.get("/presets/preset-1")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "preset-1"
    assert data["name"] == "Preset"
    assert data["category"] == PresetCategory.EXPORT.value
    assert data["description"] == "Export preset"
