# Quiz System Backend

FastAPI backend foundation with clean architecture for hosting video processing, AI integrations, and storage services.

## Features

- **FastAPI Framework**: Modern, fast (high-performance) web framework
- **Clean Architecture**: Organized package structure with separation of concerns
- **Environment Configuration**: Type-safe settings management with Pydantic
- **Logging**: Structured logging with Loguru
- **CORS Support**: Configured for Flutter/Web clients
- **Health Check**: Basic health and project info endpoints

## Project Structure

```
backend/
├── app/
│   ├── api/              # API routes and dependencies
│   ├── core/             # Core functionality (config, logging)
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   ├── workers/          # Background workers
│   ├── repositories/     # Data access layer
│   ├── utils/            # Utility functions
│   └── main.py           # FastAPI application entry point
├── tests/                # Test files
├── storage/              # File storage (git-ignored)
├── logs/                 # Application logs (git-ignored)
├── .env                  # Environment variables (git-ignored)
├── .env.example          # Environment variables template
├── pyproject.toml        # Poetry dependencies
├── poetry.lock           # Poetry lock file
├── Makefile              # Development commands
└── README.md             # This file
```

## Requirements

- Python 3.12+
- Poetry (for dependency management)

## Installation

1. **Clone the repository** (if not already done)

2. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

3. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

4. **Install dependencies**:
   ```bash
   make install
   # or
   poetry install
   ```

5. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Configuration

All configuration is managed through environment variables. See `.env.example` for available options:

### Required Variables

- `OPENAI_API_KEY`: Your OpenAI API key for AI features

### Optional Variables

- `APP_NAME`: Application name (default: "Quiz System Backend")
- `APP_VERSION`: Application version (default: "0.1.0")
- `DEBUG`: Debug mode (default: false)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `CORS_ORIGINS`: Comma-separated list of allowed origins
- `DATABASE_URL`: Database connection string (default: sqlite:///./storage/app.db)
- `STORAGE_ROOT`: Path for file storage (default: ./storage)
- `UPLOAD_MAX_SIZE`: Maximum upload size in bytes (default: 104857600 = 100MB)
- `FFMPEG_THREADS`: Number of FFmpeg threads (default: 2)
- `VIDEO_OUTPUT_FORMAT`: Video output format (default: mp4)
- `WORKER_CONCURRENCY`: Number of background workers processing jobs (default: 4)
- `MAX_QUEUE_SIZE`: Maximum pending jobs before enqueueing blocks (default: 100)
- `JOB_MAX_ATTEMPTS`: Default attempts before a job is marked failed (default: 3)
- `JOB_RETRY_DELAY_SECONDS`: Delay in seconds before retrying a failed job (default: 5)
- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_FILE`: Log file path (default: ./logs/app.log)

## Running the Application

### Development Server

Start the development server with auto-reload:

```bash
make dev
# or
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- Main API: http://localhost:8000
- API Documentation (Swagger): http://localhost:8000/docs
- Alternative API Documentation (ReDoc): http://localhost:8000/redoc

### Production Server

For production, use:

```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Health Check

```bash
GET /health
```

Returns the health status of the application.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00"
}
```

### Project Info

```bash
GET /info
```

Returns project metadata including name, version, and debug status.

**Response:**
```json
{
  "name": "Quiz System Backend",
  "version": "0.1.0",
  "debug": false
}
```

## Storage & Video Uploads

Large video files are stored on disk under the directory configured by `STORAGE_ROOT` (defaults to `./storage`). The following structure is created automatically:

```
storage/
├── uploads/       # Raw uploads streamed from clients
├── processed/     # Future transcoded/optimized outputs
├── thumbnails/    # Generated thumbnail images or placeholders
├── exports/       # Final exports and downloads
├── music/         # Project specific music/voiceover assets
└── metadata/      # JSON metadata registry (video_assets.json)
```

Each project receives its own folder inside the `uploads/`, `processed/`, `thumbnails/`, `exports/`, and `music/` directories. File names are sanitized and suffixed with a hash to avoid collisions while remaining deterministic.

### Upload Endpoint

```
POST /projects/{project_id}/videos
Content-Type: multipart/form-data
Form field name: file
```

- Streams the uploaded file using 4MB chunks via `aiofiles`
- Validates video format (`.mp4`, `.mov`, `.avi`)
- Registers metadata in `storage/metadata/video_assets.json`
- Kicks off thumbnail generation and metadata extraction stubs.

**Successful Response:**
```json
{
  "asset_id": "uuid",
  "filename": "20250101T123000-abc123.mp4",
  "original_filename": "lesson.mp4",
  "size_bytes": 1048576,
  "project_id": "demo",
  "status": "ready"
}
```

### Listing & Deleting Assets

- `GET /projects/{project_id}/videos` — list stored assets for a project.
- `DELETE /projects/{project_id}/videos/{asset_id}` — remove a single asset and its files.
- `DELETE /projects/{project_id}/storage` — wipe all stored files and metadata for a project (used during project deletion workflows).

### Storage Statistics

```
GET /storage/stats
GET /projects/{project_id}/storage/stats
```

The global endpoint reports totals across all projects, while the project-specific variant drills down into a single project's storage usage to monitor capacity and plan cleanups.

### Disk Usage Notes

- The storage directory is ignored by git (`backend/.gitignore`).
- Ensure sufficient disk space before processing large batches of videos.
- Periodically review `storage/metadata/video_assets.json` and the `storage/.../project_*` directories for unused assets.

## Background Job Processing

Long-running video and AI operations run asynchronously via a lightweight job queue built on `asyncio` workers.

- Jobs are persisted to `storage/metadata/jobs.json` for durability across restarts.
- Workers are bootstrapped during FastAPI startup using the concurrency and queue size specified by `WORKER_CONCURRENCY` and `MAX_QUEUE_SIZE`.
- Default handlers are provided for `ingest`, `scene_detection`, `transcription`, and `export` flows inside `app/workers/handlers.py`.
- Automatic retries honour `JOB_MAX_ATTEMPTS` and `JOB_RETRY_DELAY_SECONDS`, capturing error details and re-queueing work until the attempt budget is exhausted.
- Structured lifecycle logs and progress metrics are published with every state change for rich observability.

### Enqueueing Jobs

```
POST /projects/{project_id}/jobs
{
  "job_type": "ingest",
  "payload": {
    "asset_id": "..."
  },
  "max_attempts": 5,
  "retry_delay_seconds": 10
}
```

The response contains the job identifier, status, and initial metadata. Newly created jobs enter the `queued` state and are automatically picked up by the background workers. The optional `max_attempts` and `retry_delay_seconds` fields let clients override the global defaults per job.

### Monitoring Jobs

- `GET /projects/{project_id}/jobs` — list jobs for a project, optionally filtered via `?status=queued&status=running`.
- `GET /projects/{project_id}/jobs/{job_id}` — retrieve the latest status, progress percentage, logs, and results.

#### Real-time Streaming

- **Server-Sent Events** — `GET /projects/{project_id}/jobs/{job_id}/events`
- **WebSocket** — `GET /projects/{project_id}/jobs/{job_id}/ws`

Each event contains the full job payload (status, progress, logs, and results). These endpoints are ideal for dashboards that need to reflect live changes without polling.

### Running Workers

The FastAPI application starts background workers automatically, but you can also run a dedicated worker process for horizontal scaling:

```
make worker
# or
poetry run python -m app.workers.runner
```

Both the API and standalone worker share the same queue storage, so jobs continue processing no matter which process is running.

### Graceful Shutdown

During shutdown the worker queue drains outstanding tasks, cancels scheduled retries, and persists any remaining queued jobs so they can resume automatically on the next startup.

## Development Commands

The Makefile provides convenient commands for development:

```bash
make help      # Show available commands
make install   # Install dependencies
make dev       # Run development server
make worker    # Run standalone background workers
make lint      # Run linting checks
make fmt       # Format code
make test      # Run tests
make clean     # Clean up generated files
```

## Dependencies

Core dependencies (defined in `pyproject.toml`):

- **fastapi**: Web framework
- **uvicorn[standard]**: ASGI server
- **sqlalchemy**: SQL toolkit and ORM
- **pydantic-settings**: Settings management
- **python-multipart**: Multipart form data support
- **aiofiles**: Async file operations
- **loguru**: Logging
- **ffmpeg-python**: FFmpeg wrapper for video processing
- **httpx**: Async HTTP client
- **openai**: OpenAI API client
- **python-dotenv**: Environment variable management
- **alembic**: Database migrations
- **websockets**: WebSocket support for real-time features
- **sse-starlette**: Server-Sent Events utilities for streaming updates

## Testing

A comprehensive `pytest` suite covers repositories, services, FastAPI endpoints, and the
background job queue. External integrations such as FFmpeg and OpenAI are stubbed so the suite
runs quickly without network or system dependencies.

### Running tests

```bash
make test
# or
poetry run pytest tests/ -v
```

### Linting & Formatting

Linting and formatting are enforced with Ruff, Black, and isort:

```bash
make lint   # run Ruff checks plus Black/isort in --check mode
make fmt    # auto-format imports and code
```

### Test fixtures

- Temporary SQLite databases and isolated storage trees are created automatically for each test.
- Sample audio/video payloads are generated on the fly for upload and pipeline scenarios.
- Job queue helpers provide deterministic execution without long-lived background workers.

## Logging

Logs are written to:
- **Console**: Colored output for development
- **File**: Rotating log files in `./logs/` directory (if configured)

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

## Architecture

The application follows a clean architecture pattern:

- **API Layer** (`api/`): HTTP endpoints and request handling
- **Service Layer** (`services/`): Business logic and orchestration
- **Repository Layer** (`repositories/`): Data access and persistence
- **Models** (`models/`): Database models
- **Schemas** (`schemas/`): Data validation and serialization
- **Workers** (`workers/`): Background job processing
- **Utils** (`utils/`): Shared utilities and helpers

## Next Steps

- Implement video processing service
- Add AI integration endpoints
- Set up database models and migrations
- Implement file storage service
- Add authentication and authorization
- Create worker queues for background processing

## License

[Your License Here]
