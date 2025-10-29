from __future__ import annotations

import importlib
from typing import Any, Dict, List, Sequence, Tuple

from backend.app.services.ai.providers.base import (
    BaseAIProvider,
    ProviderError,
    ProviderNotConfiguredError,
    ProviderRateLimitError,
    ProviderResponse,
    ProviderUsage,
)


class ClaudeProvider(BaseAIProvider):
    """Adapter for Anthropic's Claude models."""

    name = "claude"
    default_chat_model = "claude-3-5-sonnet-20240620"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._client: Any | None = None

    # ------------------------------------------------------------------
    # Base hooks
    # ------------------------------------------------------------------
    def _is_configured(self) -> bool:
        api_key = getattr(self.settings, "anthropic_api_key", None)
        if not api_key:
            return False
        try:
            importlib.import_module("anthropic")
        except ImportError:
            self.logger.warning("Anthropic SDK not installed; disabling provider.")
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
        system_prompt, converted_messages = self._convert_messages(messages)
        if system_prompt:
            payload.setdefault("system", system_prompt)
        payload.setdefault("max_tokens", 1024)
        try:
            response = client.messages.create(model=model, messages=converted_messages, **payload)
        except Exception as exc:  # pragma: no cover - requires SDK
            raise self._translate_exception(exc) from exc
        content = self._extract_text(response)
        usage = self._extract_usage(response, model)
        return ProviderResponse(provider=self.name, content=content, usage=usage, raw=response)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client
        api_key = getattr(self.settings, "anthropic_api_key", None)
        if not api_key:
            raise ProviderNotConfiguredError(self.name)
        module = importlib.import_module("anthropic")
        client_cls = getattr(module, "Anthropic", None)
        if client_cls is None:
            raise ProviderError(self.name, "Anthropic client class not available.", retryable=False)
        self._client = client_cls(api_key=api_key)
        return self._client

    def _convert_messages(self, messages: Sequence[Dict[str, str]]) -> Tuple[str | None, List[Dict[str, Any]]]:
        system_parts: List[str] = []
        converted: List[Dict[str, Any]] = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if role == "system":
                system_parts.append(str(content))
                continue
            mapped_role = role if role in {"user", "assistant"} else "user"
            converted.append({"role": mapped_role, "content": str(content)})
        system_prompt = "\n".join(system_parts) if system_parts else None
        return system_prompt, converted

    def _extract_text(self, response: Any) -> str:
        contents = getattr(response, "content", None)
        if isinstance(contents, list):
            parts: List[str] = []
            for part in contents:
                if hasattr(part, "text"):
                    parts.append(getattr(part, "text") or "")
                elif isinstance(part, dict):
                    parts.append(str(part.get("text", "")))
            return "".join(parts)
        if isinstance(response, dict):
            content = response.get("content", [])
            if isinstance(content, list):
                texts = []
                for item in content:
                    if isinstance(item, dict):
                        texts.append(str(item.get("text", "")))
                return "".join(texts)
            return str(content)
        return str(response)

    def _extract_usage(self, response: Any, model: str) -> ProviderUsage:
        usage = ProviderUsage(model=model)
        usage_obj = getattr(response, "usage", None)
        if usage_obj is not None:
            usage.prompt_tokens = getattr(usage_obj, "input_tokens", None)
            usage.completion_tokens = getattr(usage_obj, "output_tokens", None)
            usage.total_tokens = getattr(usage_obj, "total_tokens", None)
        elif isinstance(response, dict):
            payload = response.get("usage", {})
            usage.prompt_tokens = payload.get("input_tokens")
            usage.completion_tokens = payload.get("output_tokens")
            usage.total_tokens = payload.get("total_tokens")
        return usage

    def _translate_exception(self, exc: Exception) -> ProviderError:
        status = getattr(exc, "status_code", None) or getattr(exc, "http_status", None)
        code = getattr(exc, "error_code", None) or getattr(exc, "code", None)
        message = getattr(exc, "message", None) or str(exc) or "Claude request failed."
        lower_message = message.lower()
        if status == 429 or "rate limit" in lower_message:
            return ProviderRateLimitError(self.name, message, code=code, status_code=status)
        retryable_status = {408, 409, 425, 500, 502, 503, 504}
        retryable = status in retryable_status if status is not None else "temporarily" in lower_message
        return ProviderError(self.name, message, code=code, status_code=status, retryable=retryable)


__all__ = ["ClaudeProvider"]
