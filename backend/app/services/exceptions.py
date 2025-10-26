from __future__ import annotations

from typing import Any, Optional


class AIServiceError(RuntimeError):
    """Base exception for AI integration failures."""

    def __init__(self, message: str, *, retryable: bool = False, context: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.context = context or {}

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "message": str(self),
            "retryable": self.retryable,
        }
        if self.context:
            payload["context"] = self.context
        return payload


class AIMissingConfigurationError(AIServiceError):
    """Raised when mandatory configuration is missing."""

    def __init__(self, message: str, context: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, retryable=False, context=context)


class AINonRetryableError(AIServiceError):
    """Raised when the operation should not be retried automatically."""

    def __init__(self, message: str, context: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, retryable=False, context=context)


class AIRetryableError(AIServiceError):
    """Raised for transient failures that are safe to retry."""

    def __init__(self, message: str, context: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, retryable=True, context=context)


__all__ = [
    "AIServiceError",
    "AIMissingConfigurationError",
    "AINonRetryableError",
    "AIRetryableError",
]
