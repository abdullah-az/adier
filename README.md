# Quiz System Platform

A multi-experience learning platform that pairs a FastAPI backend with both a Flutter client and a React preview tool. The backend powers media processing pipelines, AI-assisted authoring, and storage services, while the Flutter frontend delivers the primary learner experience.

## Repository Layout

```
.
├── backend/           # FastAPI application (Poetry managed)
├── frontend/cto/      # Flutter application
├── prisma/            # Prisma schema used by the React tooling
├── src/               # React 18 + Vite preview experience
├── setup.bat          # One-time Windows setup script
├── start-backend.bat  # Windows helper to run the FastAPI server
├── start-frontend.bat # Windows helper to run the Flutter app
├── start-all.bat      # Windows helper to launch backend + frontend
└── stop-all.bat       # Windows helper to stop running processes
```

## Prerequisites

- **Python 3.10+** (used by the FastAPI backend)
- **Flutter 3.9+** (bundles the required Dart SDK)
- **Node.js 18+** (for the React tooling and Prisma client)
- **FFmpeg** available on your `PATH`
- **Git** (for cloning and keeping the repo up-to-date)

> ℹ️ The batch scripts included in this repository verify that Python, Flutter, and FFmpeg are available before they start.

## Windows Quick Start

These scripts live in the repository root and can be double-clicked from File Explorer. Each script prints colourised status messages and pauses on failure so you never miss an error.

### 1. Run the one-time setup

1. Double-click **`setup.bat`**.
2. The script will:
   - Validate that Python, Flutter, and FFmpeg are installed.
   - Create a virtual environment for the backend (`backend/.venv`).
   - Install backend dependencies with Poetry and provision storage/log directories.
   - Run database migrations when an Alembic configuration is present.
   - Install Flutter dependencies (`flutter pub get`).
   - Create `.env` and `backend/.env` from `.env.example` if they are missing.
3. Update the generated `backend/.env` to include your real `OPENAI_API_KEY`.

### 2. Launch the platform

- **All services:** double-click **`start-all.bat`**. Two terminals will open—one for the FastAPI backend and one for the Flutter frontend.
- **Backend only:** double-click **`start-backend.bat`**.
- **Frontend only:** double-click **`start-frontend.bat`** (auto-detects the Windows desktop device and falls back to Chrome when necessary).

Each script keeps its console window open so you can see logs in real time. Close the window or press `Ctrl+C` when you want to stop a service.

### 3. Stop everything

- Double-click **`stop-all.bat`** to close the launcher windows and terminate lingering `uvicorn`, `flutter`, and `dart` processes.

## Environment Variables

An updated `.env.example` sits in the repository root. Copy it to `.env` (the setup script does this automatically) and review the inline documentation:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

Key values to configure:

- `OPENAI_API_KEY` – required for AI-powered features.
- `DATABASE_URL` – MySQL connection string shared by the backend and Prisma tooling (override inside `backend/.env` if you prefer SQLite for local development).
- `FFMPEG_PATH` – optional override when FFmpeg is not on your `PATH`.
- `VITE_API_URL` – URL your React preview should use to reach the backend (defaults to `http://localhost:8000`).

## Working on macOS or Linux

The batch files target Windows users. On macOS/Linux you can run the projects manually:

- Backend: `cd backend && poetry install && poetry run uvicorn app.main:app --reload`
- Flutter: `cd frontend/cto && flutter pub get && flutter run`
- React preview: `npm install && npm run dev`

Refer to the dedicated READMEs inside `backend/` and `frontend/cto/` for deeper details on architecture, troubleshooting, and advanced workflows.
