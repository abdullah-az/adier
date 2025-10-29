from __future__ import annotations

import logging

from fastapi import FastAPI

from .api import api_router
from .core.config import Settings, get_settings
from .core.logging import configure_logging

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings: Settings = get_settings()
    configure_logging(settings)

    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.state.settings = settings

    app.include_router(api_router)

    @app.on_event("startup")
    async def log_startup() -> None:
        logger.info(
            "Application startup complete",
            extra={"environment": settings.environment},
        )

    return app


app = create_app()

__all__ = ["create_app", "app"]
