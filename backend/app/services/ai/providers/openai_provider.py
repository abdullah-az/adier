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


class OpenAIProvider(BaseAIProvider):
    """Adapter for OpenAI's APIs."""

    name = "openai"
    default_chat_model = "gpt-4o-mini"
    default_embedding_model = "text-embedding-3-small"
    default_transcription_model = "whisper-1"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._client: Any | None = None

    # ------------------------------------------------------------------
    # Base hooks
    # ------------------------------------------------------------------
    def _is_configured(self) -> bool:
        api_key = getattr(self.settings, "openai_api_key", None)
        if not api_key:
            return False
        try:
            importlib.import_module("openai")
        except ImportError:
            self.logger.warning("OpenAI SDK not installed; disabling provider.")
            return False
        return True

    @property
    def supports_embeddings(self) -> bool:
        return True

    @property
    def supports_transcription(self) -> bool:
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

    def _generate_embedding_impl(self, text: Sequence[str] | str, call_options: Dict[str, Any]) -> ProviderResponse:
        client = self._ensure_client()
        payload = dict(call_options)
        model = payload.pop("model", self.default_embedding_model)
        try:
            response = client.embeddings.create(model=model, input=text, **payload)
        except Exception as exc:  # pragma: no cover - requires SDK
            raise self._translate_exception(exc) from exc
        usage = ProviderUsage(model=model)
        usage.metadata["embedding_count"] = len(text) if isinstance(text, Sequence) and not isinstance(text, str) else 1
        usage_data = getattr(response, "usage", None)
        if usage_data:
            usage.prompt_tokens = getattr(usage_data, "prompt_tokens", None)
            usage.total_tokens = getattr(usage_data, "total_tokens", None)
        elif isinstance(response, dict):
            metadata = response.get("usage", {})
            usage.prompt_tokens = metadata.get("prompt_tokens")
            usage.total_tokens = metadata.get("total_tokens")
        return ProviderResponse(provider=self.name, content="", usage=usage, raw=response)

    def _transcribe_impl(self, audio_path: str, call_options: Dict[str, Any]) -> ProviderResponse:
        client = self._ensure_client()
        payload = dict(call_options)
        model = payload.pop("model", self.default_transcription_model)
        try:
            with open(audio_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(model=model, file=audio_file, **payload)
        except FileNotFoundError as exc:
            raise ProviderError(self.name, f"Audio file not found: {audio_path}", retryable=False) from exc
        except Exception as exc:  # pragma: no cover - requires SDK
            raise self._translate_exception(exc) from exc
        text = self._extract_transcript_text(response)
        usage = ProviderUsage(model=model)
        return ProviderResponse(provider=self.name, content=text, usage=usage, raw=response)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client
        api_key = getattr(self.settings, "openai_api_key", None)
        if not api_key:
            raise ProviderNotConfiguredError(self.name)
        module = importlib.import_module("openai")
        client_cls = getattr(module, "OpenAI", None)
        if client_cls is None:
            raise ProviderError(self.name, "OpenAI client class not available.", retryable=False)
        self._client = client_cls(api_key=api_key)
        return self._client

    def _translate_exception(self, exc: Exception) -> ProviderError:
        status = getattr(exc, "status_code", None) or getattr(exc, "http_status", None)
        code = getattr(exc, "code", None)
        if code is None and hasattr(exc, "error") and isinstance(exc.error, dict):
            code = exc.error.get("code")
        message = getattr(exc, "message", None) or str(exc) or "OpenAI request failed."
        lower_message = message.lower()
        if status == 429 or "rate limit" in lower_message:
            return ProviderRateLimitError(self.name, message, code=code, status_code=status)
        retryable_status = {408, 409, 425, 429, 500, 502, 503, 504}
        retryable = status in retryable_status if status is not None else "temporarily" in lower_message
        return ProviderError(self.name, message, code=code, status_code=status, retryable=retryable)

    def _extract_choice_content(self, response: Any) -> str:
        choices = getattr(response, "choices", None)
        if isinstance(choices, list) and choices:
            first = choices[0]
            message = getattr(first, "message", None)
            if message is None and isinstance(first, dict):
                message = first.get("message") or first.get("delta")
            if message is None:
                return getattr(first, "text", "") if not isinstance(first, dict) else first.get("text", "")
            if isinstance(message, dict):
                return str(message.get("content", ""))
            return getattr(message, "content", "")
        if isinstance(response, dict):
            choices = response.get("choices", [])
            if choices:
                first = choices[0]
                if isinstance(first, dict):
                    message = first.get("message") or first.get("delta", {})
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
        choices = getattr(response, "choices", None)
        if isinstance(choices, list) and choices:
            first = choices[0]
            finish_reason = getattr(first, "finish_reason", None)
            if finish_reason is None and isinstance(first, dict):
                finish_reason = first.get("finish_reason")
            if finish_reason:
                usage.metadata["finish_reason"] = finish_reason
        return usage

    def _extract_transcript_text(self, response: Any) -> str:
        if hasattr(response, "text"):
            return getattr(response, "text")
        if isinstance(response, dict):
            return str(response.get("text") or response.get("transcript", ""))
        return str(response)


__all__ = ["OpenAIProvider"]
