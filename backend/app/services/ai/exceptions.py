class AIProviderError(RuntimeError):
    """Base class for AI provider failures."""


class AIProviderConfigurationError(AIProviderError):
    """Raised when a provider is misconfigured or missing credentials."""


class AIProviderNotAvailableError(AIProviderError):
    """Raised when no provider can be used for a requested capability."""


class AIProviderRateLimitError(AIProviderError):
    """Raised when a provider signals it has hit a rate limit."""
