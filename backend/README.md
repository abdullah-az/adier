# Backend - FastAPI Service

This directory will contain the FastAPI-based REST API for video processing, project management, and AI-powered editing features.

## Planned Structure

- `app/` - Application source code
  - `main.py` - FastAPI application entry point
  - `api/` - API endpoints and routes
  - `models/` - Database models
  - `schemas/` - Pydantic schemas for request/response validation
  - `services/` - Business logic and video processing services
  - `core/` - Core configuration and utilities
  - `db/` - Database connection and session management
- `tests/` - Pytest test suites
- `alembic/` - Database migration scripts
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variable template

## Tooling and Requirements

- Python 3.11+
- FFmpeg (installed system-wide)
- PostgreSQL or MySQL database (local or containerized)
- Redis (optional, for caching and task queues)

## Key Technologies

- **FastAPI** - Web framework with automatic OpenAPI docs
- **SQLAlchemy** - ORM for database operations
- **Pydantic** - Data validation and settings management
- **FFmpeg** - Video processing via subprocess or library wrapper
- **Pytest** - Testing framework
- **Alembic** - Database migrations

## Next Steps

1. Set up project structure with `app/` and `tests/` directories
2. Define database schema for projects, videos, and edit timelines
3. Implement core video processing endpoints (trim, merge, filter)
4. Add authentication and user management
5. Integrate asynchronous job processing for long-running video exports

Please refer to the root README for global project conventions and setup instructions.
