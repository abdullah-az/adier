from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

try:  # pragma: no cover - import guarded for safety in environments without openai
    from openai import (
        APITimeoutError,
        APIError,
        APIStatusError,
        AsyncOpenAI,
        RateLimitError,
    )
except Exception:  # pragma: no cover - openai should be installed but guard defensively
    APITimeoutError = APIError = APIStatusError = RateLimitError = Exception
    AsyncOpenAI = None  # type: ignore


class OpenAIConfigurationError(RuntimeError):
    """Raised when OpenAI cannot be used because configuration is missing."""


class OpenAIRequestError(RuntimeError):
    """Raised when an OpenAI request fails after retries."""


class OpenAIService:
    """Lightweight wrapper around the AsyncOpenAI client with retry logic."""

    def __init__(
        self,
        *,
        api_key: Optional[str],
        request_timeout: float = 120.0,
        max_retries: int = 3,
        backoff_seconds: float = 2.0,
    ) -> None:
        self.api_key = api_key
        self.request_timeout = request_timeout
        self.max_retries = max(1, max_retries)
        self.backoff_seconds = max(0.1, backoff_seconds)
        self._client: Optional[AsyncOpenAI] = None

        if api_key and AsyncOpenAI is not None:
            self._client = AsyncOpenAI(api_key=api_key, timeout=request_timeout)
            logger.info("Initialised OpenAI client", timeout=request_timeout, max_retries=max_retries)
        else:
            logger.warning("OpenAI client disabled - API key missing")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_client(self) -> AsyncOpenAI:
        if self._client is None:
            raise OpenAIConfigurationError("OpenAI API key is not configured")
        return self._client

    def _is_retryable(self, exc: Exception) -> bool:
        if isinstance(exc, (RateLimitError, APITimeoutError)):
            return True
        if isinstance(exc, APIStatusError):
            status = getattr(exc, "status_code", None)
            return bool(status and status >= 500)
        if isinstance(exc, APIError):
            status = getattr(exc, "status_code", None)
            return bool(status and status >= 500)
        status_code = getattr(exc, "status_code", None)
        if status_code is None:
            status_code = getattr(exc, "status", None)
        return bool(status_code in {408, 409, 425, 429, 500, 502, 503, 504})

    async def _with_retry(self, coro_factory):  # type: ignore[no-untyped-def]
        attempt = 0
        delay = self.backoff_seconds
        while True:
            try:
                return await coro_factory()
            except Exception as exc:  # pragma: no cover - relies on external API
                attempt += 1
                if attempt >= self.max_retries or not self._is_retryable(exc):
                    logger.error("OpenAI request failed", attempt=attempt, error=str(exc))
                    raise OpenAIRequestError(str(exc)) from exc
                logger.warning("OpenAI request retrying", attempt=attempt, delay=delay, error=str(exc))
                await asyncio.sleep(delay)
                delay *= 2

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def transcribe_audio(
        self,
        *,
        file_path: Path,
        model: str,
        language: Optional[str] = None,
    ) -> Any:
        """Call the Whisper transcription endpoint and return the raw response object."""
        client = self._ensure_client()

        async def _execute():
            with file_path.open("rb") as handle:
                return await client.audio.transcriptions.create(  # type: ignore[no-any-return]
                    model=model,
                    file=handle,
                    response_format="verbose_json",
                    language=language,
                )

        return await self._with_retry(_execute)

    async def generate_json_response(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float = 0.2,
        max_output_tokens: Optional[int] = None,
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Generate a JSON object response using the Responses API."""
        client = self._ensure_client()

        async def _execute():
            return await client.responses.create(  # type: ignore[no-any-return]
                model=model,
                input=[
                    {
                        "role": "system",
                        "content": [{"type": "text", "text": system_prompt}],
                    },
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": user_prompt}],
                    },
                ],
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                response_format={"type": "json_object"},
            )

        response = await self._with_retry(_execute)
        raw_text = getattr(response, "output_text", None)
        if raw_text is None:
            try:
                chunks = []
                for item in getattr(response, "output", []):
                    for content in getattr(item, "content", []):
                        text = getattr(content, "text", None)
                        if text is not None:
                            chunks.append(text)
                raw_text = "".join(chunks)
            except Exception:  # pragma: no cover - defensive parsing
                raw_text = None

        if not raw_text:
            raise OpenAIRequestError("OpenAI response did not contain text output")

        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError as exc:  # pragma: no cover - depends on AI output
            logger.error("Failed to parse JSON response from OpenAI", error=str(exc), output=raw_text)
            raise OpenAIRequestError("OpenAI response was not valid JSON") from exc

        usage = getattr(response, "usage", None)
        usage_dict: Dict[str, Any] = {}
        if usage:
            usage_dict = {
                "input_tokens": getattr(usage, "input_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            }

        return payload, usage_dict

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.close()  # type: ignore[func-returns-value]
