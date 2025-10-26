"""Provider orchestration logic coordinating multiple AI backends."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, Optional

from loguru import logger

from app.services.ai.base import (
    AIProvider,
    LocalFallbackProvider,
    ProviderCapabilityNotSupportedError,
    ProviderError,
    ProviderInvocationError,
    ProviderNotConfiguredError,
    ProviderQuotaError,
    ProviderRateLimitError,
    ProviderResult,
    ProviderTask,
    ProviderUnavailableError,
)
from app.repositories.provider_repository import ProviderConfigRepository


@dataclass(slots=True)
class ProviderInvocation:
    provider_id: str
    task: ProviderTask
    data: dict[str, Any]
    cost: float
    metadata: dict[str, Any]
    attempts: list[dict[str, Any]]
    currency: str = "USD"

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "provider": self.provider_id,
            "task": self.task.value,
            "result": self.data,
            "cost": {"amount": self.cost, "currency": self.currency},
            "metadata": {**self.metadata, "attempts": self.attempts},
        }
        return payload


class AIOrchestrator:
    """Select the best provider for a task and handle fallbacks gracefully."""

    def __init__(
        self,
        settings: Any,
        repository: ProviderConfigRepository,
        *,
        fallback_provider: Optional[AIProvider] = None,
    ) -> None:
        self.settings = settings
        self.repository = repository
        self.providers: dict[str, AIProvider] = {}
        self.fallback_provider = fallback_provider or LocalFallbackProvider()
        self._state: dict[str, Any] = ProviderConfigRepository.default_state()
        self._priority: list[str] = []
        self._lock = asyncio.Lock()
        self.currency = getattr(settings, "ai_cost_currency", "USD")

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------
    @classmethod
    async def create(
        cls,
        settings: Any,
        repository: ProviderConfigRepository,
        *,
        providers: Optional[Iterable[AIProvider]] = None,
        fallback_provider: Optional[AIProvider] = None,
    ) -> "AIOrchestrator":
        orchestrator = cls(settings, repository, fallback_provider=fallback_provider)
        await orchestrator._load_state()
        orchestrator.register_provider(orchestrator.fallback_provider, is_fallback=True)
        if providers:
            for provider in providers:
                orchestrator.register_provider(provider)
        await orchestrator._ensure_priority_chain()
        return orchestrator

    async def _load_state(self) -> None:
        self._state = await self.repository.load_state()
        stored_priority = self._state.get("priority") or []
        self._priority = self._sanitise_chain(stored_priority)

    async def _ensure_priority_chain(self) -> None:
        if not self._priority:
            default_chain = self._parse_priority_string(getattr(self.settings, "ai_provider_priority", ""))
            if not default_chain:
                default_chain = [pid for pid in self.providers if pid != self.fallback_provider.provider_id]
            self._priority = self._sanitise_chain(default_chain)
            await self._persist_state()

    def register_provider(self, provider: AIProvider, *, is_fallback: bool = False) -> None:
        provider_id = provider.provider_id
        self.providers[provider_id] = provider
        if provider_id not in self._state.setdefault("usage", {}):
            self._state["usage"][provider_id] = {
                "requests": 0,
                "cost": 0.0,
                "tasks": {},
                "tokens": 0,
                "last_used": None,
            }
        if is_fallback:
            if provider_id not in self._priority:
                self._priority.append(provider_id)
        logger.debug(
            "Registered AI provider",
            provider=provider_id,
            capabilities=sorted(task.value for task in provider.capabilities),
            configured=provider.is_available(),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def list_providers(self, *, include_unconfigured: bool = True) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        usage = self._state.get("usage", {})
        for provider_id, provider in self.providers.items():
            if not include_unconfigured and not provider.is_available():
                continue
            descriptor = provider.describe()
            descriptor["priority_rank"] = self._priority.index(provider_id) if provider_id in self._priority else None
            descriptor["usage"] = usage.get(provider_id, {})
            descriptor["currency"] = self.currency
            entries.append(descriptor)
        entries.sort(key=lambda entry: entry.get("priority_rank") if entry.get("priority_rank") is not None else 999)
        return entries

    def get_usage_summary(self) -> dict[str, Any]:
        usage = self._state.get("usage", {})
        return {provider_id: dict(stats) for provider_id, stats in usage.items()}

    def get_priority(self) -> list[str]:
        return list(self._priority)

    async def update_priority(self, priority: list[str]) -> list[str]:
        sanitized = self._sanitise_chain(priority)
        async with self._lock:
            self._priority = sanitized
            self._state["priority"] = list(sanitized)
            await self._persist_state()
        return list(self._priority)

    def get_project_overrides(self, project_id: str) -> dict[str, Any]:
        overrides = self._state.get("project_overrides", {}).get(project_id, {})
        return {
            "priority": list(overrides.get("priority", [])),
            "task_overrides": {
                task: list(chain)
                for task, chain in overrides.get("task_overrides", {}).items()
            },
        }

    async def set_project_overrides(
        self,
        project_id: str,
        *,
        priority: Optional[list[str]] = None,
        task_overrides: Optional[dict[str, list[str]]] = None,
    ) -> dict[str, Any]:
        async with self._lock:
            project_map = self._state.setdefault("project_overrides", {})
            if priority is None and task_overrides is None:
                project_map.pop(project_id, None)
            else:
                record: dict[str, Any] = {}
                if priority is not None:
                    record["priority"] = self._sanitise_chain(priority)
                if task_overrides:
                    task_map: dict[str, list[str]] = {}
                    for task_name, chain in task_overrides.items():
                        if isinstance(task_name, ProviderTask):
                            task_key = task_name.value
                        else:
                            task_key = ProviderTask(task_name).value
                        task_map[task_key] = self._sanitise_chain(chain)
                    record["task_overrides"] = task_map
                project_map[project_id] = record
            await self._persist_state()
        return self.get_project_overrides(project_id)

    async def analyze_scene(
        self,
        project_id: str,
        *,
        video_frames: list[Any],
        transcript: Optional[str] = None,
        **kwargs: Any,
    ) -> ProviderInvocation:
        return await self._execute(
            ProviderTask.SCENE_ANALYSIS,
            project_id,
            "analyze_scene",
            video_frames=video_frames,
            transcript=transcript,
            **kwargs,
        )

    async def transcribe_audio(
        self,
        project_id: str,
        *,
        audio_source: Any,
        language: Optional[str] = None,
        **kwargs: Any,
    ) -> ProviderInvocation:
        return await self._execute(
            ProviderTask.TRANSCRIPTION,
            project_id,
            "transcribe_audio",
            audio_source=audio_source,
            language=language,
            **kwargs,
        )

    async def generate_highlights(
        self,
        project_id: str,
        *,
        transcript: str,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ProviderInvocation:
        return await self._execute(
            ProviderTask.HIGHLIGHT_GENERATION,
            project_id,
            "generate_highlights",
            transcript=transcript,
            metadata=metadata,
            **kwargs,
        )

    async def extract_text(
        self,
        project_id: str,
        *,
        document: Any,
        **kwargs: Any,
    ) -> ProviderInvocation:
        return await self._execute(
            ProviderTask.TEXT_EXTRACTION,
            project_id,
            "extract_text",
            document=document,
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _execute(
        self,
        task: ProviderTask,
        project_id: str,
        method_name: str,
        **payload: Any,
    ) -> ProviderInvocation:
        chain = self._resolve_priority(project_id, task)
        attempts: list[dict[str, Any]] = []
        for provider_id in chain:
            provider = self.providers.get(provider_id)
            attempt_meta = {"provider": provider_id}
            if provider is None:
                attempt_meta["status"] = "missing"
                attempts.append(attempt_meta)
                continue
            if not provider.supports(task):
                attempt_meta["status"] = "unsupported"
                attempts.append(attempt_meta)
                continue
            if not provider.is_available():
                attempt_meta["status"] = "unavailable"
                attempts.append(attempt_meta)
                continue
            try:
                method = getattr(provider, method_name)
                result: ProviderResult = await method(**payload)
            except ProviderNotConfiguredError as exc:
                attempt_meta["status"] = "not_configured"
                attempt_meta["detail"] = str(exc)
            except ProviderCapabilityNotSupportedError as exc:
                attempt_meta["status"] = "unsupported"
                attempt_meta["detail"] = str(exc)
            except ProviderRateLimitError as exc:
                attempt_meta["status"] = "rate_limited"
                attempt_meta["detail"] = str(exc)
            except ProviderQuotaError as exc:
                attempt_meta["status"] = "quota_exceeded"
                attempt_meta["detail"] = str(exc)
            except ProviderInvocationError as exc:
                attempt_meta["status"] = "error"
                attempt_meta["detail"] = str(exc)
            except ProviderError as exc:
                attempt_meta["status"] = "error"
                attempt_meta["detail"] = str(exc)
            except Exception as exc:  # pragma: no cover - defensive
                attempt_meta["status"] = "exception"
                attempt_meta["detail"] = str(exc)
                logger.bind(provider=provider_id, task=task.value).exception("Unexpected provider failure")
            else:
                metadata = dict(result.metadata)
                attempt_meta_success = {"provider": provider_id, "status": "success"}
                invocation = ProviderInvocation(
                    provider_id=provider_id,
                    task=task,
                    data=dict(result.data),
                    cost=float(result.cost or 0.0),
                    metadata=metadata,
                    attempts=attempts + [attempt_meta_success],
                    currency=self.currency,
                )
                await self._record_usage(provider_id, task, invocation)
                return invocation
            attempts.append(attempt_meta)
        raise ProviderUnavailableError(task, attempts)

    def _resolve_priority(self, project_id: str, task: ProviderTask) -> list[str]:
        chain = list(self._priority)
        overrides = self._state.get("project_overrides", {}).get(project_id, {})
        task_overrides = overrides.get("task_overrides", {})
        if task.value in task_overrides:
            chain = list(task_overrides[task.value])
        elif overrides.get("priority"):
            chain = list(overrides["priority"])
        if self.fallback_provider.provider_id not in chain:
            chain.append(self.fallback_provider.provider_id)
        return self._sanitise_chain(chain)

    def _sanitise_chain(self, chain: Iterable[str]) -> list[str]:
        seen = set()
        sanitised: list[str] = []
        for provider_id in chain:
            if provider_id not in self.providers:
                continue
            if provider_id in seen:
                continue
            seen.add(provider_id)
            sanitised.append(provider_id)
        if self.fallback_provider.provider_id not in seen:
            sanitised.append(self.fallback_provider.provider_id)
        return sanitised

    def _parse_priority_string(self, value: str) -> list[str]:
        if not value:
            return []
        parts = [part.strip() for part in value.split(",")]
        return [part for part in parts if part]

    async def _record_usage(self, provider_id: str, task: ProviderTask, invocation: ProviderInvocation) -> None:
        async with self._lock:
            usage_map = self._state.setdefault("usage", {})
            provider_usage = usage_map.setdefault(
                provider_id,
                {"requests": 0, "cost": 0.0, "tasks": {}, "tokens": 0, "last_used": None},
            )
            provider_usage["requests"] += 1
            provider_usage["cost"] = round(float(provider_usage.get("cost", 0.0)) + invocation.cost, 6)
            provider_usage["last_used"] = datetime.utcnow().isoformat()
            task_usage = provider_usage.setdefault("tasks", {})
            task_stats = task_usage.setdefault(task.value, {"requests": 0, "cost": 0.0})
            task_stats["requests"] += 1
            task_stats["cost"] = round(float(task_stats.get("cost", 0.0)) + invocation.cost, 6)

            usage_metadata = invocation.metadata.get("usage") if isinstance(invocation.metadata, dict) else None
            if isinstance(usage_metadata, dict):
                tokens = (
                    usage_metadata.get("total_tokens")
                    or usage_metadata.get("totalTokens")
                    or usage_metadata.get("tokens")
                )
                if tokens:
                    provider_usage["tokens"] = provider_usage.get("tokens", 0) + int(tokens)

            await self._persist_state()

    async def _persist_state(self) -> None:
        self._state["priority"] = list(self._priority)
        await self.repository.save_state(self._state)
