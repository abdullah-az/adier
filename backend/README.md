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
- `DATABASE_URL`: Database connection string
- `STORAGE_PATH`: Path for file storage (default: ./storage)
- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_FILE`: Log file path (default: ./logs/app.log)

## Running the Application

### Database & Migrations

The backend uses SQLite by default (configurable via `DATABASE_URL`). To create the schema and apply migrations:

```bash
# Create the migrations folder (first time only)
poetry run alembic upgrade head
```

To generate a new migration after changing models:

```bash
DATABASE_URL=sqlite:///./quiz_system.db poetry run alembic revision --autogenerate -m "add_new_feature"
poetry run alembic upgrade head
```

You can also run the lightweight initialization script (for local development) which builds tables using the ORM metadata:

```bash
poetry run python scripts/init_db.py
```

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

## Development Commands

The Makefile provides convenient commands for development:

```bash
make help      # Show available commands
make install   # Install dependencies
make dev       # Run development server
make lint      # Run linting checks
make format    # Format code
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

## Testing

Tests will be organized in the `tests/` directory (to be implemented).

```bash
make test
# or
poetry run pytest tests/ -v
```

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

## Database Schema

The application includes the following entities with relationships:

- **Project**: Top-level container for video editing projects
- **VideoAsset**: Uploaded video files with metadata (duration, resolution, codec)
- **SceneDetection**: Detected scenes within videos
- **SubtitleSegment**: Subtitle/caption segments for projects or clips
- **TimelineClip**: Clips arranged on the video editing timeline
- **AudioTrack**: Audio tracks (voice-over, music, effects)
- **BackgroundMusic**: Background music tracks for projects
- **ExportJob**: Video export jobs with progress tracking
- **JobProgress**: Progress logs for export jobs

All tables include appropriate indexes for efficient lookups on foreign keys and frequently queried fields.

## Next Steps

- Implement video processing service
- Add AI integration endpoints
- Implement file storage service
- Add authentication and authorization
- Create worker queues for background processing
- Build API endpoints for CRUD operations on all entities

## License

[Your License Here]
