from __future__ import annotations

import logging
from celery import Celery

from ..core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

celery_app = Celery(
    "ai-video-editor",
    broker=settings.queue_broker_url,
    backend=settings.queue_result_backend,
    include=["backend.app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    task_default_queue=settings.queue_default_name,
    task_default_retry_delay=30,
    task_max_retries=3,
    result_expires=3600,
)

__all__ = ["celery_app"]
