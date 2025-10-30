# AI Video Editor – Smart Social Media Content Platform

An end-to-end workflow for transforming long-form recordings into polished, platform-ready short clips. The stack pairs a Flutter desktop/mobile client with a FastAPI backend, Celery workers, and modular AI providers to accelerate editing, transcription, and export.

## Features at a Glance

- **AI-assisted clip generation** with ordered fallback across OpenAI, Gemini, Claude, and Groq (see [`docs/ai-providers.md`](docs/ai-providers.md)).
- **Background media pipeline** handling ingestion, FFmpeg-based processing, and export via Redis + Celery workers.
- **Responsive Flutter client** with Riverpod state management, go_router navigation shells, and localisation hooks (`lib/l10n`).
- **Storage abstraction** supporting local filesystem by default with signed-path generation for secure downloads.
- **Health & diagnostics endpoints** for API uptime and queue observability.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quickstart](#quickstart)
3. [Project Structure](#project-structure)
4. [Environment Configuration](#environment-configuration)
5. [Testing & Quality Gates](#testing--quality-gates)
6. [Offline & Privacy Considerations](#offline--privacy-considerations)
7. [Documentation Index](#documentation-index)
8. [Localisation Roadmap](#localisation-roadmap)
9. [Contributing](#contributing)

## Prerequisites

The platform targets Python 3.11+, Flutter 3.22+, Redis 6+, and FFmpeg. Install the required toolchain per operating system.

### Windows 11 / 10

1. **Python & Git** (via Windows Package Manager):
   ```powershell
   winget install --id Python.Python.3.11 -e
   winget install --id Git.Git -e
   ```
2. **FFmpeg**: `winget install --id Gyan.FFmpeg.Full -e`
3. **Redis**: Install the [Memurai](https://www.memurai.com/download) community edition or run Redis through WSL/Docker (`docker run -p 6379:6379 redis:7`).
4. **Flutter**: Follow the [official Windows installation guide](https://docs.flutter.dev/get-started/install/windows) and ensure `flutter doctor` passes. Enable desktop support with `flutter config --enable-macos-desktop --enable-windows-desktop`.
5. **Build tools**: Install Visual Studio Build Tools with C++ workload for Python packages that need compilation.

> **Recommendation:** Use Windows Subsystem for Linux (Ubuntu) for parity with production shell scripts: `wsl --install`.

### macOS (14 Sonoma or later)

```bash
# Command Line Tools
xcode-select --install

# Package manager
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install python@3.11 redis ffmpeg
brew services start redis

# Flutter
brew install --cask flutter
flutter doctor
```

### Ubuntu 22.04 / Debian-based Linux

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip git ffmpeg redis-server build-essential

# Enable and start Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Flutter (snap)
sudo snap install flutter --classic
flutter doctor
```

> For headless servers, run Flutter in CI mode (`flutter test`, `flutter build`) without connecting devices.

## Quickstart

### 1. Backend API

```bash
# From the repository root
python3.11 -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r backend/requirements.txt

cp .env.example .env
alembic -c backend/alembic.ini upgrade head

uvicorn backend.app.main:app --reload
```

### 2. Background Workers & Queue

```bash
# Terminal 1 – ensure Redis is running (see prerequisites).
redis-cli ping  # should return PONG

# Terminal 2 – start Celery worker
source .venv/bin/activate
celery -A backend.app.workers.worker worker --loglevel=info
```

### 3. Flutter Client

```bash
cd frontend
flutter pub get
flutter run --target lib/main_development.dart --dart-define APP_FLAVOR=development
```

> Use `lib/main_staging.dart` or `lib/main_production.dart` for other flavors. Desktop builds require `flutter config --enable-windows-desktop` or equivalent OS flag.

### Smoke Test

1. Visit `http://localhost:8000/docs` to verify OpenAPI docs load.
2. Call `GET http://localhost:8000/health/diagnostics` and confirm Redis connectivity.
3. From the Flutter workspace, trigger an ingest job and watch Celery logs for status transitions.

## Project Structure

```
backend/
  app/
    api/          # FastAPI routers and route handlers
    core/         # Settings, logging, DB, and config utilities
    services/     # AI, video, and storage service layers
    workers/      # Celery app, job manager, task implementations
  tests/          # pytest suites covering services and APIs
frontend/
  lib/
    src/          # Flutter application (core, features, widgets)
    l10n/         # Localisation ARB files
  assets/config/  # Flavor configuration bundles
```

Quality analysis guidelines live in `QUALITY_ANALYSIS_IMPLEMENTATION.md`.

## Environment Configuration

Key settings are defined in `.env` (loaded by Pydantic Settings). Common values:

| Variable | Purpose |
| --- | --- |
| `APP_ENV` | `development` / `production` / `testing` toggles logging and defaults. |
| `DATABASE_URL` | SQLite by default (`sqlite:///backend/data/app.db`); replace with Postgres/MySQL for production. |
| `QUEUE_BROKER_URL`, `QUEUE_RESULT_BACKEND` | Redis broker/result endpoints. |
| `STORAGE_ROOT`, `STORAGE_TEMP` | Directories used by `StorageService`. |
| `OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `GROQ_API_KEY` | Enable respective providers. |
| `AI_PROVIDER_ORDER` | Ordered fallback list (comma-separated). |

Refer to [`docs/ai-providers.md`](docs/ai-providers.md) for exhaustive AI configuration, privacy guidance, and offline tips.

## Testing & Quality Gates

| Layer | Command | Notes |
| --- | --- | --- |
| Backend unit/integration | `python -m pytest backend/tests` | Ensure `.venv` is active and database paths are writeable. |
| Backend formatting | (Respect project conventions) | Use type hints and follow existing code style; add tools like `ruff`/`black` via PRs if needed. |
| Celery workers | `celery -A backend.app.workers.worker worker --loglevel=info` | Submit a `POST /jobs` request to validate pipeline. |
| Flutter static analysis | `flutter analyze` | Run inside `frontend/`. |
| Flutter widget tests | `flutter test` | Extend coverage for new widgets/data layers. |

CI will execute equivalent commands; fix lint/test failures before opening a pull request.

## Offline & Privacy Considerations

- Operate fully offline by leaving `AI_PROVIDER_ORDER` empty and disabling API keys. Provide custom providers for on-prem models if needed.
- Use SQLite or local Postgres, and keep `storage_root` on an encrypted volume for sensitive footage.
- Reduce log verbosity (`LOG_LEVEL=WARNING`) and prefer console format to avoid leaking PII into JSON logs.
- Rotate or scrub temporary directories (`storage_temp`) between sessions in shared environments.

More detail can be found in [`docs/README.md`](docs/README.md#offline--air-gapped-deployment-notes).

## Documentation Index

- [`docs/README.md`](docs/README.md) – Architecture overview, subsystem breakdown, testing strategy, and offline deployment notes.
- [`docs/api.md`](docs/api.md) – REST endpoints with request/response samples.
- [`docs/ai-providers.md`](docs/ai-providers.md) – AI setup, fallback logic, and privacy guidance.
- [`docs/user-guide.md`](docs/user-guide.md) – Upload → Edit → Export workflow (with screenshot placeholders).
- [`docs/contributing.md`](docs/contributing.md) – Branching, testing, and localisation guidance.

## Localisation Roadmap

- Flutter copy is generated from ARB files under `frontend/lib/l10n`. Run `flutter gen-l10n` after adding new translations.
- Future backend localisation will surface via `Accept-Language` negotiation; design APIs with locale awareness in mind.
- Include bilingual screenshots in the user guide once translations are available (see `docs/user-guide.md`).

## Contributing

Refer to [`docs/contributing.md`](docs/contributing.md) for branching strategy, testing checklists, and localisation best practices. Issues and improvement ideas are tracked alongside tickets; prefer structured discussions (ADR, design docs) for cross-cutting changes.

---

Need help? Open an issue or ping the #video-editor channel in Slack/Teams with logs and reproduction steps.
