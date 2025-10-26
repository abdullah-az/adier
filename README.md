# cto

The **cto** repository is a mono-repo that combines a Flutter front-end experience with a FastAPI backend service. Use this document as the entry point for understanding the project layout, tooling, and development workflow.

## Project structure

```
/
├── backend/         # FastAPI service and supporting libraries
├── frontend/
│   └── cto/         # Flutter application
├── docs/            # Architectural and process documentation
├── .env.example     # Root-level environment variable template
└── .gitignore       # Repository-wide ignore rules
```

Additional storage directories (for example `backend/storage/` and `backend/logs/`) are created at runtime and are intentionally gitignored.

## Prerequisites

- **Flutter** 3.35.7 or later (includes compatible Dart SDK)
- **Python** 3.12+
- **Poetry** for Python dependency management (`curl -sSL https://install.python-poetry.org | python3 -`)
- **Make** (optional but recommended for backend workflows)

## Getting started

### 1. Clone and configure env files

```bash
git clone <repo-url>
cd <repo-directory>
cp .env.example .env
```

Set `CTO_API_BASE_URL` in the root `.env` if you need to surface the backend URL to tooling or automation scripts.

### 2. Backend setup (FastAPI)

```bash
cd backend
cp .env.example .env
make install        # Installs Poetry dependencies
make dev            # Runs uvicorn with auto-reload
```

Key endpoints:
- API root: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. Frontend setup (Flutter)

```bash
cd frontend/cto
flutter pub get
flutter run         # Uses the default connected device
```

Use `flutter devices` to list available targets and `flutter run -d <device-id>` to pick a specific platform. For localization or generated files run `flutter gen-l10n` and `flutter pub run build_runner build` as needed.

## Documentation

Supplementary architecture notes, decision records, and process guides live in the [`docs/`](./docs) directory, while module-specific documents remain alongside their code (for example `backend/README.md`).

## Storage & media directories

The backend writes uploads, logs, and derived assets to `backend/storage/` and `backend/logs/`. These folders are ignored by git by default. Ensure your local environment has sufficient disk space when working with large media files.

## Contributing

1. Create a new branch from `main` (or the relevant release branch).
2. Update or create tests/documentation as appropriate.
3. Run formatters, linters, and test suites for both modules where applicable.
4. Submit a pull request for review.

Welcome to **cto** — happy building!
