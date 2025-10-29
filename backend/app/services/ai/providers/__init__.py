from __future__ import annotations

from typing import Dict, Type

from backend.app.services.ai.providers.base import (
    AllProvidersFailedError,
    BaseAIProvider,
    ProviderError,
    ProviderErrorInfo,
    ProviderFeatureNotSupportedError,
    ProviderNotConfiguredError,
    ProviderRateLimitError,
    ProviderResponse,
    ProviderTimeoutError,
    ProviderUsage,
)
from backend.app.services.ai.providers.claude_provider import ClaudeProvider
from backend.app.services.ai.providers.gemini_provider import GeminiProvider
from backend.app.services.ai.providers.groq_provider import GroqProvider
from backend.app.services.ai.providers.openai_provider import OpenAIProvider

PROVIDER_REGISTRY: Dict[str, Type[BaseAIProvider]] = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "claude": ClaudeProvider,
    "groq": GroqProvider,
}

__all__ = [
    "AllProvidersFailedError",
    "BaseAIProvider",
    "ProviderError",
    "ProviderErrorInfo",
    "ProviderFeatureNotSupportedError",
    "ProviderNotConfiguredError",
    "ProviderRateLimitError",
    "ProviderResponse",
    "ProviderTimeoutError",
    "ProviderUsage",
    "ClaudeProvider",
    "GeminiProvider",
    "GroqProvider",
    "OpenAIProvider",
    "PROVIDER_REGISTRY",
]
