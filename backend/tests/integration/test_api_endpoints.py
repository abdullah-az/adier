from __future__ import annotations

import time
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.models.pipeline import GeneratedMedia, ThumbnailInfo, TimelineCompositionRequest, TimelineCompositionResult


def _wait_for_status(client: TestClient, project_id: str, job_id: str, expected: str = "completed", timeout: float = 5.0) -> dict[str, Any]:
    deadline = time.time() + timeout
    while time.time() < deadline:
        response = client.get(f"/projects/{project_id}/jobs/{job_id}")
        response.raise_for_status()
        payload = response.json()
        if payload["status"] == expected:
            return payload
        time.sleep(0.05)
    raise AssertionError(f"Job {job_id} did not reach '{expected}' within {timeout} seconds")


def _upload_video(client: TestClient, project_id: str, video_bytes: bytes) -> dict[str, Any]:
    response = client.post(
        f"/projects/{project_id}/videos",
        files={"file": ("sample.mp4", video_bytes, "video/mp4")},
    )
    response.raise_for_status()
    return response.json()


def test_video_upload_listing_and_stats(client: TestClient, sample_video_bytes: bytes):
    project_id = "integration"

    upload_payload = _upload_video(client, project_id, sample_video_bytes)
    asset_id = upload_payload["asset_id"]

    list_response = client.get(f"/projects/{project_id}/videos")
    list_response.raise_for_status()
    assets = list_response.json()
    assert any(asset["id"] == asset_id for asset in assets)

    project_stats_response = client.get(f"/projects/{project_id}/storage/stats")
    project_stats_response.raise_for_status()
    project_stats = project_stats_response.json()
    assert project_stats["project_id"] == project_id
    assert "uploads" in project_stats["categories"]

    global_stats_response = client.get("/storage/stats")
    global_stats_response.raise_for_status()
    global_stats = global_stats_response.json()
    assert "categories" in global_stats
    assert global_stats["categories"]["uploads"]["file_count"] >= 1

    delete_response = client.delete(f"/projects/{project_id}/storage")
    assert delete_response.status_code == 204

    refreshed_list_response = client.get(f"/projects/{project_id}/videos")
    refreshed_list_response.raise_for_status()
    assert refreshed_list_response.json() == []


@pytest.mark.parametrize("job_type", ["scene_detection", "transcription"])
def test_background_job_lifecycle(client: TestClient, job_type: str):
    project_id = f"job-{job_type}"
    response = client.post(
        f"/projects/{project_id}/jobs",
        json={"job_type": job_type, "payload": {"asset_id": "asset-42"}},
    )
    response.raise_for_status()
    job = response.json()

    completed = _wait_for_status(client, project_id, job["id"])
    assert completed["status"] == "completed"
    assert completed["result"]

    list_completed = client.get(f"/projects/{project_id}/jobs", params={"status": "completed"}).json()
    assert any(item["id"] == job["id"] for item in list_completed)


def test_export_job_uses_pipeline_stub(client: TestClient, sample_video_bytes: bytes, monkeypatch: pytest.MonkeyPatch):
    project_id = "export-demo"
    asset_payload = _upload_video(client, project_id, sample_video_bytes)

    pipeline = client.app.state.pipeline_service

    async def stub_compose(
        self,
        project: str,
        request: TimelineCompositionRequest,
        *,
        log=None,
        progress=None,
    ) -> TimelineCompositionResult:
        if log is not None:
            await log("stub-pipeline", {"clips": len(request.clips)})
        if progress is not None:
            await progress(92.0, "finalising exports")
        safe_project = project.replace("..", "").replace("/", "_").strip() or "project"
        return TimelineCompositionResult(
            timeline=GeneratedMedia(
                asset_id="timeline-1",
                name="Timeline",
                category="processed",
                relative_path=f"processed/{safe_project}/timeline.mp4",
                metadata={"duration": 12.0},
            ),
            proxy=None,
            exports=[
                GeneratedMedia(
                    asset_id="export-1",
                    name="YouTube Shorts",
                    category="exports",
                    relative_path=f"exports/{safe_project}/shorts.mp4",
                    metadata={"profile": "default"},
                )
            ],
            thumbnails=[
                ThumbnailInfo(
                    path=f"thumbnails/{safe_project}/timeline.jpg",
                    clip_index=None,
                    timestamp=0.5,
                    context="timeline",
                )
            ],
        )

    monkeypatch.setattr(type(pipeline), "compose_timeline", stub_compose)

    request_payload = {
        "timeline": {
            "clips": [
                {
                    "asset_id": asset_payload["asset_id"],
                    "in_point": 0.0,
                    "out_point": 1.0,
                }
            ],
            "generate_thumbnails": True,
        }
    }

    response = client.post(
        f"/projects/{project_id}/jobs",
        json={"job_type": "export", "payload": request_payload},
    )
    response.raise_for_status()
    job = response.json()

    completed = _wait_for_status(client, project_id, job["id"])
    assert completed["status"] == "completed"
    assert completed["result"]["exports"][0]["asset_id"] == "export-1"
    assert completed["result"]["thumbnails"]
