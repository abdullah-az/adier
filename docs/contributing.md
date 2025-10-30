# Contributing Guide

Thank you for helping improve the AI Video Editor platform! This document outlines the expectations for code contributions, testing, and documentation so we can maintain a healthy, fast-moving project.

## Workflow & Branching

1. **Create a feature branch** from `main` (e.g., `feature/<ticket-key>-short-description`). This repository often uses task-specific branches (see ticket instructions) — follow the naming convention supplied by the project lead when available.
2. **Reference the ticket** in your pull request description and commits. Summaries should explain *why* the change is necessary, not only *what* changed.
3. **Rebase over merge** to keep history linear. Coordinate with the team if a feature branch lives for more than a couple of days to avoid drift.

## Development Environment

- **Backend**: Python 3.11, virtual environment recommended. Install dependencies with `pip install -r backend/requirements.txt`.
- **Frontend**: Flutter 3.22+ with the stable channel. Run `flutter pub get` inside `frontend/` after switching branches.
- **Infrastructure dependencies**: Redis (queue broker), FFmpeg (worker pipeline), and a writable storage directory (`backend/storage` by default). Use Docker Compose or local services depending on preference.
- **Environment variables**: Copy `.env.example` to `.env` and tailor keys, storage, and AI provider order. Avoid committing real API keys.

## Coding Standards

- Follow Python typing conventions (`from __future__ import annotations`, `Annotated` types where helpful) as seen across the backend package.
- Prefer repository/service abstractions instead of direct ORM access inside route handlers.
- Flutter code should remain null-safe and leverage Riverpod providers rather than singletons for mutable state.
- Keep functions and widgets small; compose UI pieces from reusable components under `lib/src/widgets` when possible.
- Avoid speculative comments. If behaviour requires clarification, extend tests or documentation.

## Testing Expectations

Before submitting a pull request:

- Run `python -m pytest backend/tests` (ensure Redis-dependent tests are skipped or mocked when offline).
- Run `flutter analyze` and `flutter test` inside the `frontend/` directory.
- If you modify Celery tasks or job orchestration, exercise the worker manually: `celery -A backend.app.workers.worker worker --loglevel=info` and submit a smoke job.
- Add or update tests alongside new behaviour. Regressions are often caught by extending existing fixtures.

## Documentation & Localisation

- Update relevant docs under `/docs/` whenever APIs, configuration, or workflows change. Include diagrams or flow descriptions as needed.
- Bilingual support is handled through Flutter ARB files (`frontend/lib/l10n`). When adding UI copy, provide English keys and open a follow-up issue to translate into additional locales.
- For backend text surfaced to users, consider adding locale-aware wrappers so future localisation work is straightforward.

## Pull Request Checklist

- [ ] Branch rebased on latest `main`.
- [ ] Linting/tests pass locally for backend and frontend.
- [ ] Documentation and changelog updated when applicable.
- [ ] Screenshots or recordings attached for UI changes (desktop + mobile form factors recommended).
- [ ] Security/compliance reviewed when enabling new AI providers or handling user data.

## Communication

Use the project Slack/Teams channel (or issue comments) to flag blocking dependencies early. For larger architectural discussions, propose an ADR (Architecture Decision Record) under `/docs/adr/` (create the directory if needed) to keep the decision trail accessible.

Happy shipping! 🚀
