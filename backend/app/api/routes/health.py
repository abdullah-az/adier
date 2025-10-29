from __future__ import annotations

import logging

from fastapi import APIRouter
from redis import Redis
from redis.exceptions import RedisError

from ...core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", summary="Service health check")
async def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }


@router.get("/diagnostics", summary="Extended diagnostics including queue status")
async def diagnostics() -> dict[str, object]:
    settings = get_settings()
    
    queue_status = _check_queue_connection(settings.queue_broker_url)
    
    return {
        "status": "ok" if queue_status["connected"] else "degraded",
        "app": settings.app_name,
        "environment": settings.environment,
        "queue": queue_status,
    }


def _check_queue_connection(broker_url: str) -> dict[str, object]:
    """Check Redis queue connection health."""
    try:
        redis_client = Redis.from_url(broker_url, socket_connect_timeout=2, socket_timeout=2)
        redis_client.ping()
        info = redis_client.info()
        return {
            "connected": True,
            "broker_url": broker_url.split("@")[-1],
            "redis_version": info.get("redis_version", "unknown"),
            "connected_clients": info.get("connected_clients", 0),
        }
    except RedisError as exc:
        logger.warning("Queue connection check failed", extra={"error": str(exc)})
        return {
            "connected": False,
            "broker_url": broker_url.split("@")[-1],
            "error": str(exc),
        }
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected error during queue connection check")
        return {
            "connected": False,
            "broker_url": broker_url.split("@")[-1],
            "error": f"Unexpected error: {str(exc)}",
        }
