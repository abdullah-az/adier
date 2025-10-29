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


class GeminiProvider(BaseAIProvider):
    """Adapter for Google Gemini models via the generative AI SDK."""

    name = "gemini"
    default_chat_model = "models/gemini-1.5-flash"
    default_embedding_model = "models/embedding-001"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._sdk: Any | None = None

    # ------------------------------------------------------------------
    # Base hooks
    # ------------------------------------------------------------------
    def _is_configured(self) -> bool:
        api_key = getattr(self.settings, "gemini_api_key", None)
        if not api_key:
            return False
        try:
            importlib.import_module("google.generativeai")
        except ImportError:
            self.logger.warning("Google Gemini SDK not installed; disabling provider.")
            return False
        return True

    @property
    def supports_embeddings(self) -> bool:
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
        sdk = self._ensure_sdk()
        payload = dict(call_options)
        model_name = payload.pop("model", self.default_chat_model)
        generative_model = sdk.GenerativeModel(model_name)
        prompt = self._convert_messages_to_prompt(messages)
        try:
            response = generative_model.generate_content(prompt, **payload)
        except Exception as exc:  # pragma: no cover - requires SDK
            raise self._translate_exception(exc) from exc
        content = self._extract_text(response)
        usage = self._extract_usage(response, model_name)
        return ProviderResponse(provider=self.name, content=content, usage=usage, raw=response)

    def _generate_embedding_impl(self, text: Sequence[str] | str, call_options: Dict[str, Any]) -> ProviderResponse:
        sdk = self._ensure_sdk()
        payload = dict(call_options)
        model_name = payload.pop("model", self.default_embedding_model)
        try:
            if isinstance(text, str):
                response = sdk.embed_content(model=model_name, content=text, **payload)
            else:
                response = sdk.embed_content(model=model_name, texts=list(text), **payload)
        except Exception as exc:  # pragma: no cover - requires SDK
            raise self._translate_exception(exc) from exc
        usage = ProviderUsage(model=model_name)
        usage.metadata["embedding_count"] = len(text) if isinstance(text, Sequence) and not isinstance(text, str) else 1
        return ProviderResponse(provider=self.name, content="", usage=usage, raw=response)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _ensure_sdk(self) -> Any:
        if self._sdk is not None:
            return self._sdk
        api_key = getattr(self.settings, "gemini_api_key", None)
        if not api_key:
            raise ProviderNotConfiguredError(self.name)
        module = importlib.import_module("google.generativeai")
        module.configure(api_key=api_key)
        self._sdk = module
        return self._sdk

    def _convert_messages_to_prompt(self, messages: Sequence[Dict[str, str]]) -> str:
        parts = [f"{message['role']}: {message['content']}" for message in messages]
        return "\n".join(parts)

    def _extract_text(self, response: Any) -> str:
        if hasattr(response, "text"):
            return response.text or ""
        if hasattr(response, "candidates"):
            candidates = getattr(response, "candidates", [])
            if candidates:
                first = candidates[0]
                if hasattr(first, "content") and hasattr(first.content, "parts"):
                    texts = [getattr(part, "text", "") for part in first.content.parts]
                    return "".join(texts)
                if isinstance(first, dict):
                    content = first.get("content", {})
                    if isinstance(content, dict):
                        parts = content.get("parts", [])
                        texts = [getattr(part, "text", "") if not isinstance(part, dict) else part.get("text", "") for part in parts]
                        return "".join(texts)
        if isinstance(response, dict):
            return str(response.get("text", ""))
        return ""

    def _extract_usage(self, response: Any, model_name: str) -> ProviderUsage:
        usage = ProviderUsage(model=model_name)
        metadata = getattr(response, "usage_metadata", None)
        if metadata:
            usage.prompt_tokens = getattr(metadata, "prompt_token_count", None)
            usage.completion_tokens = getattr(metadata, "candidates_token_count", None)
            if usage.prompt_tokens and usage.completion_tokens:
                usage.total_tokens = usage.prompt_tokens + usage.completion_tokens
        elif isinstance(response, dict):
            meta = response.get("usage_metadata", {})
            usage.prompt_tokens = meta.get("prompt_token_count")
            usage.completion_tokens = meta.get("candidates_token_count")
            if usage.prompt_tokens and usage.completion_tokens:
                usage.total_tokens = usage.prompt_tokens + usage.completion_tokens
        return usage

    def _translate_exception(self, exc: Exception) -> ProviderError:
        status = getattr(exc, "code", None)
        status_code = getattr(exc, "status_code", None) or getattr(exc, "http_status", None)
        message = getattr(exc, "message", None) or str(exc) or "Gemini request failed."
        lower_message = message.lower()
        if status_code == 429 or "resource exhausted" in lower_message or "rate limit" in lower_message:
            return ProviderRateLimitError(self.name, message, code=str(status or "rate_limit"), status_code=status_code)
        retryable_status = {408, 409, 425, 500, 502, 503, 504}
        retryable = status_code in retryable_status if status_code is not None else "temporarily" in lower_message
        return ProviderError(self.name, message, code=str(status) if status else None, status_code=status_code, retryable=retryable)


__all__ = ["GeminiProvider"]
