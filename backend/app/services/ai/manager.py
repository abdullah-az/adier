from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Iterable, Optional, Sequence

from loguru import logger

from app.core.config import Settings
from app.repositories.provider_preference_repository import ProviderPreferenceRepository
from .base import AIProvider
from .exceptions import (
    AIProviderConfigurationError,
    AIProviderError,
    AIProviderNotAvailableError,
    AIProviderRateLimitError,
)
from .models import AICapability, AIUsage, ProviderAttempt, ProviderSummary
from .providers.claude_provider import ClaudeProvider
from .providers.gemini_provider import GeminiProvider
from .providers.groq_provider import GroqProvider
from .providers.local_whisper_provider import LocalWhisperProvider
from .providers.openai_provider import OpenAIProvider


@dataclass
class ProviderRecord:
    provider: AIProvider

    @property
    def name(self) -> str:
        return self.provider.name

    @property
    def priority(self) -> int:
        return self.provider.priority

    @property
    def rate_limit_per_minute(self) -> float | None:
        return self.provider.rate_limit_per_minute


class ProviderUsageTracker:
    def __init__(self) -> None:
        self._usage: dict[str, AIUsage] = {}
        self._lock = asyncio.Lock()

    async def record(self, provider_name: str, usage: AIUsage) -> None:
        usage_clone = usage.clone()
        async with self._lock:
            current = self._usage.get(provider_name)
            if current is None:
                self._usage[provider_name] = usage_clone
            else:
                current.merge(usage_clone)

    async def snapshot(self) -> dict[str, dict[str, Any]]:
        async with self._lock:
            return {name: usage.clone().to_dict() for name, usage in self._usage.items()}


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, ProviderRecord] = {}

    def register(self, provider: AIProvider) -> None:
        record = ProviderRecord(provider=provider)
        self._providers[provider.name] = record
        provider.log_configuration()

    def get(self, name: str) -> Optional[AIProvider]:
        record = self._providers.get(name)
        return record.provider if record else None

    def providers(self) -> Sequence[AIProvider]:
        return tuple(record.provider for record in self._providers.values())

    def iter_records(self) -> Iterable[ProviderRecord]:
        return tuple(self._providers.values())


class AIManager:
    """Coordinate AI provider selection, fallback, and accounting."""

    def __init__(
        self,
        *,
        settings: Optional[Settings] = None,
        preference_repository: Optional[ProviderPreferenceRepository] = None,
        providers: Optional[Sequence[AIProvider]] = None,
    ) -> None:
        self.settings = settings
        self.registry = ProviderRegistry()
        self.preferences = preference_repository
        self._usage_tracker = ProviderUsageTracker()
        self._priority_overrides = self._parse_priority_overrides(settings.ai_provider_priority) if settings else {}
        if providers:
            for provider in providers:
                self.register_provider(provider)
        elif settings is not None:
            self._initialize_from_settings(settings)

    # ------------------------------------------------------------------
    # Provider registration & inspection
    # ------------------------------------------------------------------
    def register_provider(self, provider: AIProvider) -> None:
        override_priority = self._priority_overrides.get(provider.name)
        if override_priority is not None:
            provider.priority = override_priority
        self.registry.register(provider)

    def list_registered_providers(self) -> Sequence[str]:
        return tuple(sorted(provider.name for provider in self.registry.providers()))

    async def list_providers(self) -> list[dict[str, Any]]:
        usage_snapshot = await self._usage_tracker.snapshot()
        providers = sorted(self.registry.providers(), key=lambda provider: provider.priority)
        response: list[dict[str, Any]] = []
        for provider in providers:
            response.append(
                {
                    "name": provider.name,
                    "display_name": provider.display_name,
                    "priority": provider.priority,
                    "capabilities": sorted(capability.value for capability in provider.capabilities),
                    "configured": provider.is_configured(),
                    "available": provider.is_available(),
                    "rate_limit_per_minute": provider.rate_limit_per_minute,
                    "usage": usage_snapshot.get(provider.name, {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "audio_seconds": 0.0,
                        "cost": 0.0,
                        "requests": 0,
                    }),
                }
            )
        return response

    # ------------------------------------------------------------------
    # Preference management
    # ------------------------------------------------------------------
    async def get_preferences(self, project_id: str) -> dict[str, str]:
        if self.preferences is None:
            return {}
        return await self.preferences.get_preferences(project_id)

    async def set_preferences(self, project_id: str, preferences: dict[str, Optional[str]]) -> dict[str, str]:
        if self.preferences is None:
            raise AIProviderConfigurationError("Preference repository is not configured")

        validated: dict[str, str] = {}
        for capability_name, provider_name in preferences.items():
            if not provider_name:
                continue
            try:
                capability = AICapability(capability_name)
            except ValueError as exc:
                raise AIProviderConfigurationError(f"Unknown capability '{capability_name}'") from exc

            provider = self.registry.get(provider_name)
            if provider is None:
                raise AIProviderConfigurationError(f"Provider '{provider_name}' is not registered")
            if not provider.supports(capability):
                raise AIProviderConfigurationError(
                    f"Provider '{provider_name}' does not support capability '{capability.value}'"
                )
            validated[capability.value] = provider.name

        return await self.preferences.set_preferences(project_id, validated)

    # ------------------------------------------------------------------
    # Capability execution
    # ------------------------------------------------------------------
    async def run_scene_detection(
        self,
        project_id: str,
        video_path: Path,
        *,
        preferred_providers: Optional[Iterable[str]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        path = Path(video_path)

        async def executor(provider: AIProvider) -> tuple[Any, AIUsage]:
            return await provider.analyze_scene(path, project_id=project_id, **kwargs)

        scenes, summary = await self._execute(
            capability=AICapability.SCENE_ANALYSIS,
            project_id=project_id,
            executor=executor,
            preferred_providers=preferred_providers,
        )
        return {"provider": summary.to_dict(), "scenes": scenes}

    async def run_transcription(
        self,
        project_id: str,
        audio_path: Path,
        *,
        preferred_providers: Optional[Iterable[str]] = None,
        language: Optional[str] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        path = Path(audio_path)

        async def executor(provider: AIProvider) -> tuple[Any, AIUsage]:
            return await provider.transcribe_audio(path, project_id=project_id, language=language, **kwargs)

        transcript, summary = await self._execute(
            capability=AICapability.TRANSCRIPTION,
            project_id=project_id,
            executor=executor,
            preferred_providers=preferred_providers,
        )
        payload = dict(transcript)
        payload["provider"] = summary.to_dict()
        return payload

    async def generate_highlights(
        self,
        project_id: str,
        transcript: str,
        *,
        preferred_providers: Optional[Iterable[str]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        async def executor(provider: AIProvider) -> tuple[Any, AIUsage]:
            return await provider.generate_highlights(transcript, project_id=project_id, **kwargs)

        highlights, summary = await self._execute(
            capability=AICapability.HIGHLIGHT_GENERATION,
            project_id=project_id,
            executor=executor,
            preferred_providers=preferred_providers,
        )
        return {"provider": summary.to_dict(), **dict(highlights)}

    async def extract_text(
        self,
        project_id: str,
        image_paths: Sequence[Path],
        *,
        preferred_providers: Optional[Iterable[str]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        paths = [Path(path) for path in image_paths]

        async def executor(provider: AIProvider) -> tuple[Any, AIUsage]:
            return await provider.extract_text(paths, project_id=project_id, **kwargs)

        text, summary = await self._execute(
            capability=AICapability.TEXT_EXTRACTION,
            project_id=project_id,
            executor=executor,
            preferred_providers=preferred_providers,
        )
        payload = dict(text)
        payload["provider"] = summary.to_dict()
        return payload

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _execute(
        self,
        *,
        capability: AICapability,
        project_id: str,
        executor: Callable[[AIProvider], Awaitable[tuple[Any, AIUsage]]],
        preferred_providers: Optional[Iterable[str]] = None,
    ) -> tuple[Any, ProviderSummary]:
        providers = await self._resolve_provider_chain(capability, project_id, preferred_providers)
        if not providers:
            raise AIProviderNotAvailableError(f"No provider available for capability '{capability.value}'")

        attempts: list[ProviderAttempt] = []
        last_error: Optional[Exception] = None

        for provider in providers:
            if not provider.is_available():
                attempts.append(ProviderAttempt(provider=provider.name, status="skipped", error="not_available"))
                continue

            try:
                result_data, usage = await executor(provider)
            except AIProviderRateLimitError as exc:
                attempts.append(ProviderAttempt(provider=provider.name, status="rate_limited", error=str(exc)))
                last_error = exc
                continue
            except AIProviderError as exc:
                attempts.append(ProviderAttempt(provider=provider.name, status="error", error=str(exc)))
                last_error = exc
                continue
            except Exception as exc:  # pragma: no cover - defensive guard
                attempts.append(ProviderAttempt(provider=provider.name, status="error", error=str(exc)))
                last_error = exc
                continue

            success_attempts = attempts + [ProviderAttempt(provider=provider.name, status="success")]
            summary = ProviderSummary(
                name=provider.name,
                display_name=provider.display_name,
                capability=capability,
                attempts=success_attempts,
                usage=usage.clone(),
            )
            await self._usage_tracker.record(provider.name, usage)
            return result_data, summary

        error_message = last_error or AIProviderNotAvailableError(
            f"All providers failed for capability '{capability.value}'"
        )
        raise AIProviderNotAvailableError(str(error_message))

    async def _resolve_provider_chain(
        self,
        capability: AICapability,
        project_id: str,
        preferred_providers: Optional[Iterable[str]],
    ) -> list[AIProvider]:
        seen: set[str] = set()
        ordered: list[AIProvider] = []

        def add_provider(name: str) -> None:
            normalized = name.strip().lower()
            if not normalized or normalized in seen:
                return
            provider = self.registry.get(normalized)
            if provider is None or not provider.supports(capability):
                return
            ordered.append(provider)
            seen.add(normalized)

        for name in self._normalize_names(preferred_providers):
            add_provider(name)

        if self.preferences is not None:
            project_preferences = await self.preferences.get_preferences(project_id)
            override_name = project_preferences.get(capability.value)
            if override_name:
                add_provider(override_name)

        registry_order = sorted(
            self.registry.providers(),
            key=lambda provider: provider.priority,
        )
        for provider in registry_order:
            add_provider(provider.name)

        return ordered

    @staticmethod
    def _normalize_names(names: Optional[Iterable[str]]) -> list[str]:
        if not names:
            return []
        normalized = []
        for name in names:
            if not name:
                continue
            normalized.append(str(name).strip().lower())
        return normalized

    @staticmethod
    def _parse_priority_overrides(raw: Optional[str]) -> dict[str, int]:
        if not raw:
            return {}
        mapping: dict[str, int] = {}
        for index, name in enumerate(raw.split(",")):
            stripped = name.strip().lower()
            if stripped:
                mapping[stripped] = index
        return mapping

    @staticmethod
    def _parse_rate_limits(raw: Optional[str]) -> dict[str, float]:
        if not raw:
            return {}
        mapping: dict[str, float] = {}
        for entry in raw.split(","):
            if not entry:
                continue
            if ":" not in entry:
                continue
            name, value = entry.split(":", 1)
            try:
                mapping[name.strip().lower()] = float(value)
            except ValueError:
                continue
        return mapping

    def _initialize_from_settings(self, settings: Settings) -> None:
        rate_limits = self._parse_rate_limits(getattr(settings, "ai_provider_rate_limits", None))

        if settings.openai_api_key:
            self.register_provider(
                OpenAIProvider(
                    settings.openai_api_key,
                    model=settings.openai_model,
                    transcription_model=settings.openai_transcription_model,
                    priority=self._priority_overrides.get("openai", 100),
                    rate_limit_per_minute=rate_limits.get("openai"),
                )
            )

        if getattr(settings, "gemini_api_key", None):
            self.register_provider(
                GeminiProvider(
                    settings.gemini_api_key,
                    model=settings.gemini_model,
                    priority=self._priority_overrides.get("gemini", 120),
                    rate_limit_per_minute=rate_limits.get("gemini"),
                )
            )

        if getattr(settings, "claude_api_key", None):
            self.register_provider(
                ClaudeProvider(
                    settings.claude_api_key,
                    model=settings.claude_model,
                    priority=self._priority_overrides.get("claude", 140),
                    rate_limit_per_minute=rate_limits.get("claude"),
                )
            )

        if getattr(settings, "groq_api_key", None):
            self.register_provider(
                GroqProvider(
                    settings.groq_api_key,
                    transcription_model=settings.groq_transcription_model,
                    priority=self._priority_overrides.get("groq", 160),
                    rate_limit_per_minute=rate_limits.get("groq"),
                )
            )

        if getattr(settings, "ai_allow_local_fallback", True):
            binary_path = Path(settings.whispercpp_binary_path) if settings.whispercpp_binary_path else None
            model_path = Path(settings.whispercpp_model_path) if settings.whispercpp_model_path else None
            self.register_provider(
                LocalWhisperProvider(
                    whisper_binary=binary_path,
                    model_path=model_path,
                    priority=self._priority_overrides.get("local", 1000),
                    rate_limit_per_minute=rate_limits.get("local"),
                )
            )


def create_ai_manager(settings: Settings) -> AIManager:
    repository = ProviderPreferenceRepository(settings.storage_path)
    manager = AIManager(settings=settings, preference_repository=repository)
    logger.info(
        "AI providers initialised",
        providers=manager.list_registered_providers(),
    )
    return manager
