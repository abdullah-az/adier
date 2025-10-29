from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Optional, Sequence

from backend.app.core.config import Settings
from backend.app.services.ai.providers import (
    PROVIDER_REGISTRY,
    AllProvidersFailedError,
    BaseAIProvider,
    ProviderError,
    ProviderErrorInfo,
    ProviderNotConfiguredError,
    ProviderResponse,
)


class AIProviderRouter:
    """Coordinates AI provider calls with ordered fallback behaviour."""

    def __init__(
        self,
        settings: Settings,
        *,
        providers: Optional[Dict[str, BaseAIProvider]] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.settings = settings
        self.logger = logger or logging.getLogger("backend.app.services.ai.router")
        self.timeout = getattr(settings, "ai_provider_timeout_seconds", 30.0)
        self.max_retries = getattr(settings, "ai_provider_retries", 1)
        self.backoff_base = getattr(settings, "ai_provider_retry_base_delay", 0.5)
        self.backoff_factor = getattr(settings, "ai_provider_retry_backoff_factor", 2.0)
        self._providers = providers or self._initialise_providers()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_text(
        self,
        *,
        prompt: Optional[str] = None,
        messages: Optional[Sequence[Dict[str, str]]] = None,
        provider_order: Optional[Sequence[str]] = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        errors: List[ProviderErrorInfo] = []
        tried: List[str] = []
        for provider in self._iter_providers(provider_order):
            tried.append(provider.name)
            self.logger.debug(
                "Attempting provider",
                extra={"extra": {"provider": provider.name, "operation": "generate_text"}},
            )
            try:
                return provider.generate_text(prompt=prompt, messages=messages, **kwargs)
            except ProviderNotConfiguredError as exc:
                self.logger.info(
                    "Skipping unconfigured provider",
                    extra={"extra": {"provider": provider.name, "reason": exc.info.message}},
                )
                continue
            except ProviderError as exc:
                errors.append(exc.info)
                self.logger.warning(
                    "Provider failed, moving to fallback",
                    extra={
                        "extra": {
                            "provider": provider.name,
                            "error": exc.info.__dict__,
                            "operation": "generate_text",
                        }
                    },
                )
                continue
        if not errors and not tried:
            message = "No AI providers are configured or available."
            errors.append(ProviderErrorInfo(provider="router", message=message, retryable=False))
        raise AllProvidersFailedError(errors)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _initialise_providers(self) -> Dict[str, BaseAIProvider]:
        providers: Dict[str, BaseAIProvider] = {}
        for name, provider_cls in PROVIDER_REGISTRY.items():
            try:
                provider = provider_cls(
                    self.settings,
                    timeout=self.timeout,
                    max_retries=self.max_retries,
                    backoff_base=self.backoff_base,
                    backoff_factor=self.backoff_factor,
                )
            except Exception as exc:  # pragma: no cover - defensive, requires SDK
                self.logger.exception("Failed to initialise provider %s", name, exc_info=exc)
                continue
            providers[name] = provider
        return providers

    def _iter_providers(self, override_order: Optional[Sequence[str]]) -> Iterable[BaseAIProvider]:
        seen: set[str] = set()
        order = override_order or getattr(self.settings, "ai_provider_order", list(PROVIDER_REGISTRY.keys()))
        for name in order:
            key = (name or "").lower().strip()
            if not key or key in seen:
                continue
            seen.add(key)
            provider = self._providers.get(key)
            if provider is None:
                self.logger.debug("Requested provider '%s' is not registered.", key)
                continue
            if not provider.is_enabled:
                self.logger.info(
                    "Provider disabled, skipping",
                    extra={"extra": {"provider": provider.name, "operation": "generate_text"}},
                )
                continue
            yield provider

    @property
    def providers(self) -> Dict[str, BaseAIProvider]:
        return dict(self._providers)

    def available_providers(self) -> List[str]:
        return [name for name, provider in self._providers.items() if provider.is_enabled]


__all__ = ["AIProviderRouter"]
