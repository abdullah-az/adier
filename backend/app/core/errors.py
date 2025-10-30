from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base exception for application-level errors."""

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ResourceNotFoundError(AppException):
    """Exception raised when a resource is not found."""

    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(f"{resource} with ID '{identifier}' not found", status.HTTP_404_NOT_FOUND)
        self.resource = resource
        self.identifier = identifier


class ValidationError(AppException):
    """Exception raised for validation errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class ConflictError(AppException):
    """Exception raised for conflicting operations."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status.HTTP_409_CONFLICT)


def create_error_response(
    status_code: int,
    error: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a standardized error response."""
    response: dict[str, Any] = {
        "error": error,
        "message": message,
    }
    if details:
        response["details"] = details
    return response


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle application-level exceptions."""
    logger.warning(
        f"Application exception: {exc.message}",
        extra={
            "path": request.url.path,
            "status_code": exc.status_code,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            status_code=exc.status_code,
            error=exc.__class__.__name__,
            message=exc.message,
        ),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    logger.warning(
        f"HTTP exception: {exc.detail}",
        extra={
            "path": request.url.path,
            "status_code": exc.status_code,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            status_code=exc.status_code,
            error="HTTPException",
            message=str(exc.detail),
        ),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors."""
    logger.warning(
        "Validation error",
        extra={
            "path": request.url.path,
            "errors": exc.errors(),
        },
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error="ValidationError",
            message="Request validation failed",
            details={"errors": exc.errors()},
        ),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.exception(
        "Unexpected error",
        extra={
            "path": request.url.path,
            "error_type": type(exc).__name__,
        },
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="InternalServerError",
            message="An unexpected error occurred",
        ),
    )


__all__ = [
    "AppException",
    "ResourceNotFoundError",
    "ValidationError",
    "ConflictError",
    "create_error_response",
    "app_exception_handler",
    "http_exception_handler",
    "validation_exception_handler",
    "general_exception_handler",
]
