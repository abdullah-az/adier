from __future__ import annotations

import importlib
from typing import Any, Dict, Sequence

from backend.app.services.ai.providers.base import (
    BaseAIProvider,
    ProviderError,
    ProviderNotConfiguredError,
    ProviderRateLimitError,
    ProviderResponse,
    ProviderUsage,
)


class GroqProvider(BaseAIProvider):
    """Adapter for Groq's hosted large language models."""

    name = "groq"
    default_chat_model = "mixtral-8x7b-32768"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._client: Any | None = None

    # ------------------------------------------------------------------
    # Base hooks
    # ------------------------------------------------------------------
    def _is_configured(self) -> bool:
        api_key = getattr(self.settings, "groq_api_key", None)
        if not api_key:
            return False
        try:
            importlib.import_module("groq")
        except ImportError:
            self.logger.warning("Groq SDK not installed; disabling provider.")
            return False
        return True

    # ------------------------------------------------------------------
    # Provider implementations
    # ------------------------------------------------------------------
    def _generate_text_impl(
        self,
        messages: Sequence[Dict[str, str]],
        call_options: Dict[str, Any],
    ) -> ProviderResponse:
        if not self.is_enabled:
            raise ProviderNotConfiguredError(self.name)
        client = self._ensure_client()
        payload = dict(call_options)
        model = payload.pop("model", self.default_chat_model)
        try:
            response = client.chat.completions.create(model=model, messages=list(messages), **payload)
        except Exception as exc:  # pragma: no cover - requires SDK
            raise self._translate_exception(exc) from exc
        content = self._extract_choice_content(response)
        usage = self._extract_usage(response, model)
        return ProviderResponse(provider=self.name, content=content, usage=usage, raw=response)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client
        api_key = getattr(self.settings, "groq_api_key", None)
        if not api_key:
            raise ProviderNotConfiguredError(self.name)
        module = importlib.import_module("groq")
        client_cls = getattr(module, "Groq", None)
        if client_cls is None:
            raise ProviderError(self.name, "Groq client class not available.", retryable=False)
        self._client = client_cls(api_key=api_key)
        return self._client

    def _extract_choice_content(self, response: Any) -> str:
        choices = getattr(response, "choices", None)
        if isinstance(choices, list) and choices:
            first = choices[0]
            message = getattr(first, "message", None)
            if message is None and isinstance(first, dict):
                message = first.get("message")
            if isinstance(message, dict):
                return str(message.get("content", ""))
            if message is not None:
                return getattr(message, "content", "")
            if isinstance(first, dict):
                return str(first.get("text", ""))
        if isinstance(response, dict):
            choices = response.get("choices", [])
            if choices:
                first = choices[0]
                if isinstance(first, dict):
                    message = first.get("message", {})
                    if isinstance(message, dict):
                        return str(message.get("content", ""))
                    return str(first.get("text", ""))
        return ""

    def _extract_usage(self, response: Any, model: str) -> ProviderUsage:
        usage = ProviderUsage(model=model)
        usage_obj = getattr(response, "usage", None)
        if usage_obj is not None:
            usage.prompt_tokens = getattr(usage_obj, "prompt_tokens", None)
            usage.completion_tokens = getattr(usage_obj, "completion_tokens", None)
            usage.total_tokens = getattr(usage_obj, "total_tokens", None)
        elif isinstance(response, dict):
            payload = response.get("usage", {})
            usage.prompt_tokens = payload.get("prompt_tokens")
            usage.completion_tokens = payload.get("completion_tokens")
            usage.total_tokens = payload.get("total_tokens")
        return usage

    def _translate_exception(self, exc: Exception) -> ProviderError:
        status = getattr(exc, "status_code", None) or getattr(exc, "http_status", None)
        code = getattr(exc, "code", None)
        message = getattr(exc, "message", None) or str(exc) or "Groq request failed."
        lower_message = message.lower()
        if status == 429 or "rate limit" in lower_message:
            return ProviderRateLimitError(self.name, message, code=code, status_code=status)
        retryable_status = {408, 409, 425, 500, 502, 503, 504}
        retryable = status in retryable_status if status is not None else "temporarily" in lower_message
        return ProviderError(self.name, message, code=code, status_code=status, retryable=retryable)


__all__ = ["GroqProvider"]
