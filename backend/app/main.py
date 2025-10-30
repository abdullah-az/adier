from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from .api import api_router
from .core.config import Settings, get_settings
from .core.errors import (
    AppException,
    app_exception_handler,
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from .core.logging import configure_logging

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings: Settings = get_settings()
    configure_logging(settings)

    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.state.settings = settings

    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

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
