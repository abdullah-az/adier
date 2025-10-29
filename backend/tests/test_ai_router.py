from __future__ import annotations

import pytest

from backend.app.core.config import TestingSettings
from backend.app.services.ai import AIProviderRouter
from backend.app.services.ai.providers import (
    AllProvidersFailedError,
    BaseAIProvider,
    OpenAIProvider,
    ProviderError,
    ProviderResponse,
)


class _BaseTestProvider(BaseAIProvider):
    """Utility base provider for testing."""

    def __init__(self, settings: TestingSettings, *, response_text: str = "", retryable: bool = False, fail: bool = False):
        self._response_text = response_text
        self._fail = fail
        self._retryable = retryable
        self.calls = 0
        super().__init__(settings, timeout=0, max_retries=0, backoff_base=0, backoff_factor=1)

    def _is_configured(self) -> bool:
        return True

    def _generate_text_impl(self, messages, call_options):  # type: ignore[override]
        self.calls += 1
        if self._fail:
            raise ProviderError(self.name, "forced failure", retryable=self._retryable)
        return ProviderResponse(provider=self.name, content=self._response_text)


class FailingProvider(_BaseTestProvider):
    name = "primary"

    def __init__(self, settings: TestingSettings):
        super().__init__(settings, fail=True)


class SuccessfulProvider(_BaseTestProvider):
    name = "secondary"

    def __init__(self, settings: TestingSettings, *, response_text: str = "ok"):
        super().__init__(settings, response_text=response_text)


class AnotherProvider(_BaseTestProvider):
    name = "tertiary"

    def __init__(self, settings: TestingSettings, *, response_text: str = "alt"):
        super().__init__(settings, response_text=response_text)


def test_router_fallback_to_secondary_provider() -> None:
    settings = TestingSettings(ai_provider_order=["primary", "secondary"])
    primary = FailingProvider(settings)
    secondary = SuccessfulProvider(settings, response_text="secondary-response")
    router = AIProviderRouter(settings, providers={"primary": primary, "secondary": secondary})

    response = router.generate_text(prompt="Hello")

    assert response.provider == "secondary"
    assert response.content == "secondary-response"
    assert primary.calls == 1
    assert secondary.calls == 1


def test_router_respects_configuration_order() -> None:
    settings = TestingSettings(ai_provider_order=["tertiary", "secondary", "primary"])
    tertiary = AnotherProvider(settings, response_text="third")
    secondary = SuccessfulProvider(settings, response_text="second")
    primary = FailingProvider(settings)
    router = AIProviderRouter(
        settings,
        providers={"tertiary": tertiary, "secondary": secondary, "primary": primary},
    )

    response = router.generate_text(prompt="Hi")

    assert response.provider == "tertiary"
    assert tertiary.calls == 1
    assert secondary.calls == 0
    assert primary.calls == 0


def test_router_override_order_per_request() -> None:
    settings = TestingSettings(ai_provider_order=["primary", "secondary", "tertiary"])
    primary = SuccessfulProvider(settings, response_text="primary")
    secondary = SuccessfulProvider(settings, response_text="secondary")
    tertiary = AnotherProvider(settings, response_text="tertiary")
    router = AIProviderRouter(
        settings,
        providers={"primary": primary, "secondary": secondary, "tertiary": tertiary},
    )

    response = router.generate_text(prompt="Hi", provider_order=["tertiary", "secondary"])

    assert response.provider == "tertiary"
    assert tertiary.calls == 1
    assert secondary.calls == 0
    assert primary.calls == 0


def test_router_returns_structured_errors_when_all_fail() -> None:
    settings = TestingSettings(ai_provider_order=["primary", "tertiary"])
    primary = FailingProvider(settings)
    tertiary = AnotherProvider(settings, response_text="unused")
    tertiary._fail = True
    router = AIProviderRouter(settings, providers={"primary": primary, "tertiary": tertiary})

    with pytest.raises(AllProvidersFailedError) as exc:
        router.generate_text(prompt="Hi")

    assert len(exc.value.errors) == 2
    assert {error.provider for error in exc.value.errors} == {"primary", "tertiary"}


def test_openai_provider_disabled_without_api_key() -> None:
    settings = TestingSettings(openai_api_key=None)
    provider = OpenAIProvider(settings, timeout=0, max_retries=0, backoff_base=0, backoff_factor=1)

    assert provider.is_enabled is False
