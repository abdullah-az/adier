from __future__ import annotations

import asyncio

from loguru import logger

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.workers.runtime import create_worker_runtime


async def _run_worker() -> None:
    settings = get_settings()
    runtime = create_worker_runtime(settings)
    await runtime.start()
    logger.info(
        "Standalone worker started",
        concurrency=settings.worker_concurrency,
        max_queue_size=settings.max_queue_size,
        max_attempts=settings.job_max_attempts,
        retry_delay_seconds=settings.job_retry_delay_seconds,
    )

    try:
        while True:
            await asyncio.sleep(60)
    except asyncio.CancelledError:  # pragma: no cover - cooperative shutdown
        logger.debug("Worker coroutine cancelled")
    finally:
        await runtime.stop()
        logger.info("Standalone worker stopped")


def main() -> None:
    setup_logging()
    try:
        asyncio.run(_run_worker())
    except KeyboardInterrupt:  # pragma: no cover - CLI interrupt
        logger.info("Worker shutdown requested via keyboard interrupt")
    except asyncio.CancelledError:  # pragma: no cover - defensive
        logger.info("Worker event loop cancelled")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
