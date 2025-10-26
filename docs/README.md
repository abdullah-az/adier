# cto documentation

This directory aggregates high-level documentation for the **cto** project. Use it to capture architectural decisions, onboarding notes, and process references that apply across both the Flutter frontend and FastAPI backend.

## Repository overview

- **Frontend (`frontend/cto`)**: Flutter application targeting mobile, web, and desktop platforms. Uses Riverpod, go_router, localization tooling, and Material 3 styling.
- **Backend (`backend/`)**: FastAPI service that powers AI-assisted workflows, media ingestion, and storage orchestration. Packaged with Poetry and includes a Makefile for common tasks.
- **Shared assets**: Media and storage directories (for example `backend/storage/`) are generated at runtime and ignored by git.

## Environment variables

| Scope | File | Purpose |
|-------|------|---------|
| Global | `.env` (optional) | Surface shared values such as `CTO_API_BASE_URL` for local tooling or deployment scripts. |
| Backend | `backend/.env` | Configure FastAPI (host, port, CORS, storage paths, worker limits, OpenAI keys, etc.). |

## Local development workflow

1. Start the backend API:
   ```bash
   cd backend
   make dev
   ```
2. Launch the Flutter client in a second terminal:
   ```bash
   cd frontend/cto
   flutter run
   ```
3. Adjust the Flutter app's API target to match your running backend (default `http://localhost:8000`).

## Testing

- **Backend**: `cd backend && make test` (wraps `pytest`).
- **Frontend**: `cd frontend/cto && flutter test` for unit/widget tests.

## Additional notes

- Add ADRs, sequence diagrams, or API specs to this directory as the project evolves.
- When introducing new storage locations or generated assets, ensure they are added to the repository-level `.gitignore`.
