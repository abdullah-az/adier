#!/usr/bin/env python
"""
Background worker entrypoint for processing asynchronous jobs.

This module provides the main entrypoint for running Celery workers
that process background tasks such as video ingestion, transcription,
rendering, and export.

Usage:
    Run a worker with default configuration:
        celery -A backend.app.workers.worker worker --loglevel=info

    Run with specific queue and concurrency:
        celery -A backend.app.workers.worker worker \
            --loglevel=info \
            --queues=ai-video-editor-jobs \
            --concurrency=4

    Run with auto-reload for development:
        watchfiles 'celery -A backend.app.workers.worker worker --loglevel=info' backend/app
"""
from __future__ import annotations

import logging

from ..core.config import get_settings
from ..core.logging import configure_logging
from .celery_app import celery_app
from . import tasks  # noqa: F401 - ensure task registration

settings = get_settings()
configure_logging(settings)

logger = logging.getLogger(__name__)

logger.info(
    "Worker process starting",
    extra={
        "broker": settings.queue_broker_url,
        "backend": settings.queue_result_backend,
        "default_queue": settings.queue_default_name,
    },
)

__all__ = ["celery_app"]
