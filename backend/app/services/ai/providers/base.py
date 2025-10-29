from __future__ import annotations

import logging
import math
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple, TypeVar

from backend.app.core.config import Settings


T = TypeVar("T")


@dataclass(slots=True)
class ProviderUsage:
    """Structured usage metrics returned from a provider call."""

    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    model: Optional[str] = None
    latency_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProviderResponse:
    """Normalised response for AI generation calls."""

    provider: str
    content: str
    usage: ProviderUsage = field(default_factory=ProviderUsage)
    raw: Any = None


@dataclass(slots=True)
class ProviderErrorInfo:
    """Structured error details used for diagnostics and fallbacks."""

    provider: str
    message: str
    code: Optional[str] = None
    status_code: Optional[int] = None
    retryable: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)


class ProviderError(Exception):
    """Base exception for provider failures."""

    def __init__(
        self,
        provider: str,
        message: str,
        *,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
        retryable: bool = False,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.info = ProviderErrorInfo(
            provider=provider,
            message=message,
            code=code,
            status_code=status_code,
            retryable=retryable,
            extra=extra or {},
        )


class ProviderNotConfiguredError(ProviderError):
    """Raised when a provider is requested without the necessary credentials."""

    def __init__(self, provider: str) -> None:
        super().__init__(provider, "Provider is not configured.", retryable=False)


class ProviderRateLimitError(ProviderError):
    """Raised when a provider reports rate limiting."""

    def __init__(self, provider: str, message: str, *, code: Optional[str] = None, status_code: Optional[int] = None) -> None:
        super().__init__(
            provider,
            message,
            code=code or "rate_limit_exceeded",
            status_code=status_code,
            retryable=True,
        )


class ProviderTimeoutError(ProviderError):
    """Raised when a provider request times out."""

    def __init__(self, provider: str, *, timeout: float) -> None:
        message = f"Provider request timed out after {timeout:.1f} seconds."
        super().__init__(provider, message, code="timeout", retryable=True)


class ProviderFeatureNotSupportedError(ProviderError):
    """Raised when a provider does not support a requested feature."""

    def __init__(self, provider: str, feature: str) -> None:
        super().__init__(
            provider,
            f"Provider does not support {feature}.",
            code=f"feature_not_supported_{feature}",
            retryable=False,
        )


class AllProvidersFailedError(Exception):
    """Raised when every provider in a fallback chain fails."""

    def __init__(self, errors: Sequence[ProviderErrorInfo]):
        self.errors = list(errors)
        message = "All AI providers failed to produce a response."
        super().__init__(message)

    def __str__(self) -> str:  # pragma: no cover - delegated to default repr
        return f"{super().__str__()} errors={self.errors!r}"


class BaseAIProvider(ABC):
    """Abstract base class for AI provider integrations."""

    name: str = "base"

    def __init__(
        self,
        settings: Settings,
        *,
        timeout: float = 30.0,
        max_retries: int = 1,
        backoff_base: float = 0.5,
        backoff_factor: float = 2.0,
    ) -> None:
        self.settings = settings
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = max(backoff_base, 0)
        self.backoff_factor = max(backoff_factor, 1.0)
        self.logger = logging.getLogger(f"backend.app.services.ai.providers.{self.name}")
        self._enabled = self._is_configured()
        if not self._enabled:
            self.logger.debug("Provider disabled due to missing configuration.")

    # ---------------------------------------------------------------------
    # Properties
    # ---------------------------------------------------------------------
    @property
    def is_enabled(self) -> bool:
        return self._enabled

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def generate_text(
        self,
        *,
        prompt: Optional[str] = None,
        messages: Optional[Sequence[Dict[str, str]]] = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        if not self.is_enabled:
            raise ProviderNotConfiguredError(self.name)
        normalised_messages = self._normalise_messages(prompt=prompt, messages=messages)
        operation = "generate_text"
        call_options = dict(kwargs)
        return self._execute_with_retry(operation, self._generate_text_impl, normalised_messages, call_options)

    def generate_embedding(self, *, text: Sequence[str] | str, **kwargs: Any) -> ProviderResponse:
        if not self.is_enabled:
            raise ProviderNotConfiguredError(self.name)
        if not self.supports_embeddings:
            raise ProviderFeatureNotSupportedError(self.name, "embeddings")
        operation = "generate_embedding"
        call_options = dict(kwargs)
        return self._execute_with_retry(operation, self._generate_embedding_impl, text, call_options)

    def transcribe(self, *, audio_path: str, **kwargs: Any) -> ProviderResponse:
        if not self.is_enabled:
            raise ProviderNotConfiguredError(self.name)
        if not self.supports_transcription:
            raise ProviderFeatureNotSupportedError(self.name, "transcription")
        operation = "transcribe"
        call_options = dict(kwargs)
        return self._execute_with_retry(operation, self._transcribe_impl, audio_path, call_options)

    # ------------------------------------------------------------------
    # Hooks for subclasses
    # ------------------------------------------------------------------
    @property
    def supports_embeddings(self) -> bool:
        return False

    @property
    def supports_transcription(self) -> bool:
        return False

    @abstractmethod
    def _generate_text_impl(
        self,
        messages: Sequence[Dict[str, str]],
        call_options: Dict[str, Any],
    ) -> ProviderResponse:
        """Perform the provider-specific text generation request."""

    def _generate_embedding_impl(self, text: Sequence[str] | str, call_options: Dict[str, Any]) -> ProviderResponse:  # pragma: no cover - optional for subclasses
        raise ProviderFeatureNotSupportedError(self.name, "embeddings")

    def _transcribe_impl(self, audio_path: str, call_options: Dict[str, Any]) -> ProviderResponse:  # pragma: no cover - optional for subclasses
        raise ProviderFeatureNotSupportedError(self.name, "transcription")

    def _is_configured(self) -> bool:
        """Return whether the provider has sufficient configuration to run."""
        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _execute_with_retry(
        self,
        operation: str,
        func: Callable[..., ProviderResponse],
        *args: Any,
        **kwargs: Any,
    ) -> ProviderResponse:
        attempt = 0
        while True:
            try:
                cloned_args = [self._clone_for_retry(arg) for arg in args]
                cloned_kwargs = {key: self._clone_for_retry(value) for key, value in kwargs.items()}
                start = time.perf_counter()
                result = self._execute_with_timeout(func, *cloned_args, **cloned_kwargs)
                duration = (time.perf_counter() - start) * 1000
                self._record_usage(operation, result.usage, latency_ms=duration)
                return result
            except ProviderError as exc:  # pragma: no cover - covered via subclasses/tests
                self._log_failure(operation, exc, attempt)
                if attempt >= self.max_retries or not exc.info.retryable:
                    raise exc
                sleep_time = self._compute_backoff(attempt)
                if sleep_time:
                    time.sleep(sleep_time)
                attempt += 1

    def _execute_with_timeout(
        self,
        func: Callable[..., ProviderResponse],
        *args: Any,
        **kwargs: Any,
    ) -> ProviderResponse:
        if self.timeout <= 0:
            return func(*args, **kwargs)
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=self.timeout)
            except FuturesTimeoutError as exc:
                future.cancel()
                raise ProviderTimeoutError(self.name, timeout=self.timeout) from exc

    def _normalise_messages(
        self,
        *,
        prompt: Optional[str],
        messages: Optional[Sequence[Dict[str, str]]],
    ) -> List[Dict[str, str]]:
        if messages:
            cleaned: List[Dict[str, str]] = []
            for message in messages:
                role = message.get("role")
                content = message.get("content")
                if role is None or content is None:
                    raise ValueError("Each message must include 'role' and 'content'.")
                cleaned.append({"role": str(role), "content": str(content)})
            return cleaned
        if prompt is None:
            raise ValueError("Either prompt or messages must be provided.")
        return [{"role": "user", "content": prompt}]

    def _record_usage(self, operation: str, usage: ProviderUsage, *, latency_ms: float) -> None:
        usage.latency_ms = latency_ms
        payload = asdict(usage)
        payload = {key: value for key, value in payload.items() if value not in (None, {}, [], ())}
        self.logger.info(
            "Provider call succeeded",
            extra={
                "extra": {
                    "provider": self.name,
                    "operation": operation,
                    "usage": payload,
                }
            },
        )

    def _log_failure(self, operation: str, exc: ProviderError, attempt: int) -> None:
        self.logger.warning(
            "Provider call failed",
            extra={
                "extra": {
                    "provider": self.name,
                    "operation": operation,
                    "attempt": attempt,
                    "error": asdict(exc.info),
                }
            },
        )

    def _compute_backoff(self, attempt: int) -> float:
        if self.backoff_base <= 0:
            return 0.0
        delay = self.backoff_base * math.pow(self.backoff_factor, max(attempt, 0))
        return min(delay, self.timeout if self.timeout > 0 else delay)

    def _clone_for_retry(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: self._clone_for_retry(val) for key, val in value.items()}
        if isinstance(value, list):
            return [self._clone_for_retry(item) for item in value]
        return value


__all__ = [
    "BaseAIProvider",
    "ProviderResponse",
    "ProviderUsage",
    "ProviderErrorInfo",
    "ProviderError",
    "ProviderNotConfiguredError",
    "ProviderRateLimitError",
    "ProviderTimeoutError",
    "ProviderFeatureNotSupportedError",
    "AllProvidersFailedError",
]
