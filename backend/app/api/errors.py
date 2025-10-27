from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette import status


class APIError(Exception):
    """Custom exception for returning consistent API error responses."""

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers that emit consistent payloads."""

    @app.exception_handler(APIError)
    async def handle_api_error(_: Request, exc: APIError) -> JSONResponse:  # pragma: no cover - glue
        logger.bind(code=exc.code, details=exc.details).warning(exc.message)
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        logger.debug("Validation error", errors=exc.errors())
        payload = {
            "code": "validation_error",
            "message": "Request validation failed",
            "details": {"errors": exc.errors()},
        }
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload)

    @app.exception_handler(HTTPException)
    async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
        code = getattr(exc, "headers", {}).get("x-error-code") if exc.headers else None
        payload = {
            "code": code or "http_error",
            "message": str(exc.detail) if exc.detail else exc.status_code,
            "details": {},
        }
        logger.error("HTTP error", status_code=exc.status_code, error=payload["message"])
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled application error", error=str(exc))
        payload = {
            "code": "internal_server_error",
            "message": "An unexpected error occurred",
            "details": {},
        }
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload)
