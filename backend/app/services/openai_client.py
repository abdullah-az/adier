from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Callable, Optional

from loguru import logger
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    OpenAI,
    RateLimitError,
    ServiceUnavailableError,
)

from app.services.exceptions import (
    AIMissingConfigurationError,
    AINonRetryableError,
    AIRetryableError,
)


def _coerce_usage(usage: Any) -> dict[str, Any]:
    if usage is None:
        return {}
    if isinstance(usage, dict):
        return usage
    if hasattr(usage, "model_dump"):
        return usage.model_dump()
    if hasattr(usage, "dict"):
        return usage.dict()  # type: ignore[call-arg]
    try:
        if hasattr(usage, "json"):
            return json.loads(usage.json())  # type: ignore[call-arg]
    except Exception:  # pragma: no cover - defensive
        return {}
    return {}


def _coerce_dict(payload: Any) -> dict[str, Any]:
    if payload is None:
        return {}
    if isinstance(payload, dict):
        return payload
    if hasattr(payload, "model_dump"):
        return payload.model_dump()
    if hasattr(payload, "dict"):
        return payload.dict()  # type: ignore[call-arg]
    if hasattr(payload, "json"):
        try:
            return json.loads(payload.json())  # type: ignore[call-arg]
        except Exception:  # pragma: no cover - defensive
            pass
    try:
        return json.loads(json.dumps(payload, default=lambda value: getattr(value, "__dict__", str(value))))
    except Exception:  # pragma: no cover - defensive
        return {}


class OpenAIClient:
    """Thin asynchronous wrapper around the OpenAI Python SDK with retry logic."""

    def __init__(
        self,
        *,
        api_key: Optional[str],
        organization: Optional[str] = None,
        request_timeout: float = 60.0,
        max_retries: int = 3,
    ) -> None:
        self.api_key = api_key
        self.organization = organization
        self.request_timeout = max(1.0, float(request_timeout))
        self.max_retries = max(1, int(max_retries))
        self._client: Optional[OpenAI] = None

    def _ensure_client(self) -> OpenAI:
        if not self.api_key:
            raise AIMissingConfigurationError("OpenAI API key is not configured")
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key, organization=self.organization)
        return self._client

    async def transcribe_audio(
        self,
        *,
        file_path: Path,
        model: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        temperature: float = 0.0,
        response_format: str = "verbose_json",
    ) -> dict[str, Any]:
        """Call the OpenAI Whisper endpoint and return a dictionary payload."""

        def _invoke() -> Any:
            client = self._ensure_client().with_options(timeout=self.request_timeout)
            with file_path.open("rb") as handle:
                return client.audio.transcriptions.create(
                    model=model,
                    file=handle,
                    language=language,
                    prompt=prompt,
                    response_format=response_format,
                    temperature=temperature,
                    timestamp_granularities=["segment"],
                )

        response = await self._call_with_retry("transcription", _invoke)
        payload = _coerce_dict(response)
        usage = _coerce_usage(getattr(response, "usage", None))
        if usage:
            payload.setdefault("usage", usage)
        return payload

    async def chat_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int = 1500,
        response_format: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Invoke the Chat Completions API and return the raw dictionary payload."""

        def _invoke() -> Any:
            client = self._ensure_client().with_options(timeout=self.request_timeout)
            return client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )

        response = await self._call_with_retry("chat_completion", _invoke)
        payload = _coerce_dict(response)
        usage = _coerce_usage(payload.get("usage") or getattr(response, "usage", None))
        if usage:
            payload["usage"] = usage
        return payload

    async def _call_with_retry(self, operation: str, func: Callable[[], Any]) -> Any:
        delay = 1.0
        last_error: Optional[BaseException] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return await asyncio.to_thread(func)
            except RateLimitError as exc:
                last_error = exc
                logger.warning(
                    "OpenAI rate limited",
                    operation=operation,
                    attempt=attempt,
                    max_attempts=self.max_retries,
                )
                if attempt >= self.max_retries:
                    raise AIRetryableError(
                        "OpenAI rate limit exceeded",
                        context={"operation": operation},
                    ) from exc
            except (APITimeoutError, APIError, APIConnectionError, ServiceUnavailableError) as exc:
                last_error = exc
                logger.warning(
                    "OpenAI transient error",
                    operation=operation,
                    attempt=attempt,
                    error=str(exc),
                )
                if attempt >= self.max_retries:
                    raise AIRetryableError(
                        f"OpenAI {operation} failed after retries",
                        context={"operation": operation},
                    ) from exc
            except AuthenticationError as exc:
                raise AINonRetryableError("OpenAI authentication failed") from exc
            except BadRequestError as exc:
                raise AINonRetryableError(f"OpenAI rejected request: {exc}") from exc

            await asyncio.sleep(delay)
            delay = min(delay * 2, 30.0)

        assert last_error is not None  # pragma: no cover - defensive
        raise AIRetryableError(
            f"OpenAI {operation} failed",
            context={"operation": operation, "error": str(last_error)},
        ) from last_error


__all__ = ["OpenAIClient"]
