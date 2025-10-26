from __future__ import annotations

from fastapi import status

from app.models.job import JobStatus


def test_health_and_info_endpoints(api_client, test_settings):
    client, _ = api_client

    health_response = client.get("/health")
    assert health_response.status_code == status.HTTP_200_OK
    assert health_response.json()["status"] == "healthy"

    info_response = client.get("/info")
    assert info_response.status_code == status.HTTP_200_OK
    payload = info_response.json()
    assert payload["name"] == test_settings.app_name
    assert payload["version"] == test_settings.app_version


def test_video_upload_and_management(api_client, sample_video_bytes: bytes):
    client, runtime = api_client
    project_id = "project-api"

    response = client.post(
        f"/projects/{project_id}/videos",
        files={"file": ("lesson.mp4", sample_video_bytes, "video/mp4")},
    )
    assert response.status_code == status.HTTP_201_CREATED
    upload_payload = response.json()
    asset_id = upload_payload["asset_id"]

    list_response = client.get(f"/projects/{project_id}/videos")
    assert list_response.status_code == status.HTTP_200_OK
    assets = list_response.json()
    assert len(assets) == 1
    assert assets[0]["id"] == asset_id

    project_stats = client.get(f"/projects/{project_id}/storage/stats")
    assert project_stats.status_code == status.HTTP_200_OK
    stats_payload = project_stats.json()
    assert stats_payload["categories"]["uploads"]["file_count"] == 1

    global_stats = client.get("/storage/stats")
    assert global_stats.status_code == status.HTTP_200_OK

    delete_response = client.delete(f"/projects/{project_id}/videos/{asset_id}")
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    empty_list = client.get(f"/projects/{project_id}/videos")
    assert empty_list.status_code == status.HTTP_200_OK
    assert empty_list.json() == []

    cleanup_response = client.delete(f"/projects/{project_id}/storage")
    assert cleanup_response.status_code == status.HTTP_204_NO_CONTENT

    storage_root = runtime.storage_manager.storage_root
    for category in runtime.storage_manager.categories:
        category_dir = storage_root / category
        if category_dir.exists():
            assert not any(category_dir.iterdir()), "expected category to be empty"


def test_job_endpoints_lifecycle(api_client):
    client, runtime = api_client
    project_id = "jobs-api"

    job_response = client.post(
        f"/projects/{project_id}/jobs",
        json={"job_type": "ingest", "payload": {"asset_id": "asset-1"}},
    )
    assert job_response.status_code == status.HTTP_201_CREATED
    job_payload = job_response.json()
    job_id = job_payload["id"]
    assert runtime.job_queue.enqueued[-1] == job_id
    assert job_payload["status"] == JobStatus.QUEUED

    list_response = client.get(f"/projects/{project_id}/jobs")
    assert list_response.status_code == status.HTTP_200_OK
    jobs = list_response.json()
    assert len(jobs) == 1
    assert jobs[0]["id"] == job_id

    filtered_response = client.get(f"/projects/{project_id}/jobs", params=[("status", "queued")])
    assert filtered_response.status_code == status.HTTP_200_OK
    assert filtered_response.json()[0]["status"] == JobStatus.QUEUED

    detail_response = client.get(f"/projects/{project_id}/jobs/{job_id}")
    assert detail_response.status_code == status.HTTP_200_OK
    assert detail_response.json()["id"] == job_id

    invalid_filter = client.get(f"/projects/{project_id}/jobs", params=[("status", "unknown")])
    assert invalid_filter.status_code == status.HTTP_400_BAD_REQUEST

    missing_job = client.get(f"/projects/{project_id}/jobs/non-existent")
    assert missing_job.status_code == status.HTTP_404_NOT_FOUND
