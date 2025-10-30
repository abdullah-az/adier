# API Reference

Base URL defaults to `http://localhost:8000` when running the FastAPI server locally:

```bash
uvicorn backend.app.main:app --reload
```

All responses are JSON encoded. Authentication is not enforced yet; plan to add token-based auth before production deployment.

## Health Endpoints

### `GET /health/`

Simple readiness probe returning application metadata.

**Response 200**

```json
{
  "status": "ok",
  "app": "AI Video Editor Backend",
  "environment": "development"
}
```

Use this endpoint for container orchestrator readiness/liveness checks.

### `GET /health/diagnostics`

Extended diagnostics including queue connectivity sampled via Redis `PING` and `INFO`.

**Response 200 (connected)**

```json
{
  "status": "ok",
  "app": "AI Video Editor Backend",
  "environment": "development",
  "queue": {
    "connected": true,
    "broker_url": "localhost:6379/0",
    "redis_version": "7.2.5",
    "connected_clients": 12
  }
}
```

**Response 200 (degraded)**

```json
{
  "status": "degraded",
  "app": "AI Video Editor Backend",
  "environment": "development",
  "queue": {
    "connected": false,
    "broker_url": "localhost:6379/0",
    "error": "Error 111 connecting to localhost:6379"
  }
}
```

## Job Orchestration Endpoints

Processing jobs encapsulate long-running tasks such as ingestion, transcription, clip generation, rendering, and exports. Jobs are enqueued onto Redis and executed by Celery workers.

### `POST /jobs/`

Create and enqueue a new processing job. Parameters are split between query string (metadata) and JSON body (`payload`).

| Field | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `job_type` | Query | `string` (`ingest`, `transcribe`, `generate_clip`, `render`, `export`) | ✅ | Defines the worker pipeline. |
| `clip_version_id` | Query | `string` | ❌ | Associates the job with an existing clip version for downstream updates. |
| `priority` | Query | `integer` | ❌ (default `0`) | Higher values jump the queue. |
| `payload` | Body | `object` | ✅ | Arbitrary configuration consumed by workers (e.g., file paths, AI prompt metadata). |

**Example Request**

```bash
curl -X POST "http://localhost:8000/jobs/?job_type=ingest&priority=5" \
  -H "Content-Type: application/json" \
  -d '{
        "project_id": "proj_123",
        "source_asset_id": "asset_456",
        "transcript": false
      }'
```

> **Tip:** Because `payload` is declared as a dictionary parameter, the request body becomes the job payload directly (no additional wrapper object is required). FastAPI automatically serialises it into the `payload` argument.

**Response 202**

```json
{
  "id": "job_789",
  "created_at": "2024-10-30T12:45:01.000000+00:00",
  "updated_at": "2024-10-30T12:45:01.000000+00:00",
  "clip_version_id": null,
  "job_type": "ingest",
  "status": "queued",
  "queue_name": "ai-video-editor-jobs",
  "priority": 5,
  "payload": {
    "project_id": "proj_123",
    "source_asset_id": "asset_456",
    "transcript": false
  },
  "result_payload": null,
  "error_message": null,
  "started_at": null,
  "completed_at": null
}
```

**Response 503** – Redis is unavailable or task dispatch failed.

```json
{
  "detail": "Failed to enqueue job: Queue connection error: Error 111 connecting to localhost:6379."
}
```

### `GET /jobs/{job_id}`

Fetch the latest state for a job.

**Example Request**

```bash
curl http://localhost:8000/jobs/job_789
```

**Response 200**

```json
{
  "id": "job_789",
  "created_at": "2024-10-30T12:45:01.000000+00:00",
  "updated_at": "2024-10-30T12:46:42.000000+00:00",
  "clip_version_id": null,
  "job_type": "ingest",
  "status": "in_progress",
  "queue_name": "ai-video-editor-jobs",
  "priority": 5,
  "payload": {
    "project_id": "proj_123",
    "source_asset_id": "asset_456",
    "transcript": false
  },
  "result_payload": {
    "progress": 0.42,
    "log": [
      {
        "timestamp": "2024-10-30T12:46:11.219384+00:00",
        "message": "Transcoding chunk 3/7"
      }
    ]
  },
  "error_message": null,
  "started_at": "2024-10-30T12:45:15.524113+00:00",
  "completed_at": null
}
```

**Response 404**

```json
{
  "detail": "Job job_789 not found"
}
```

Statuses transition through `pending → queued → in_progress → completed/failed/cancelled`. Subscribing clients should poll until `completed_at` or `error_message` is populated.

## Error Envelope

Errors follow FastAPI's default structure (`{"detail": "message"}`). Downstream services should surface these messages to operators and trigger retries when safe.

## WebSocket Endpoints

There are no WebSocket endpoints today. Real-time updates are achieved by polling `GET /jobs/{job_id}`. When bi-directional updates are added, they will live under `/ws/jobs/{job_id}` and follow the payload structure described above.

## Versioning Strategy

The API is currently unversioned while endpoints stabilise. Once contracts harden, expect routes to move under `/v1/`. Backwards-incompatible changes will be tracked in `CHANGELOG.md` and mirrored in the Flutter data layer.
