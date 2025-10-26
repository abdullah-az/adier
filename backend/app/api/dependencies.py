from functools import lru_cache

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.repositories.job_repository import JobRepository
from app.repositories.provider_repository import ProviderConfigRepository
from app.repositories.video_repository import VideoAssetRepository
from app.services.ai import AIOrchestrator
from app.services.job_service import JobService
from app.services.storage_service import StorageService
from app.utils.storage import StorageManager


def get_current_settings(settings: Settings = Depends(get_settings)) -> Settings:
    return settings


@lru_cache
def _storage_manager_factory(storage_path: str) -> StorageManager:
    return StorageManager(storage_root=storage_path)


@lru_cache
def _video_repository_factory(storage_path: str) -> VideoAssetRepository:
    return VideoAssetRepository(storage_root=storage_path)


@lru_cache
def _job_repository_factory(storage_path: str) -> JobRepository:
    return JobRepository(storage_root=storage_path)


def get_storage_manager(settings: Settings = Depends(get_settings)) -> StorageManager:
    """Get shared StorageManager instance."""
    return _storage_manager_factory(settings.storage_path)


def get_video_repository(settings: Settings = Depends(get_settings)) -> VideoAssetRepository:
    """Get shared VideoAssetRepository instance."""
    return _video_repository_factory(settings.storage_path)


def get_job_repository(settings: Settings = Depends(get_settings)) -> JobRepository:
    """Get shared JobRepository instance."""
    return _job_repository_factory(settings.storage_path)


def get_storage_service(
    storage_manager: StorageManager = Depends(get_storage_manager),
    video_repository: VideoAssetRepository = Depends(get_video_repository),
) -> StorageService:
    """Get StorageService instance with dependencies."""
    return StorageService(storage_manager=storage_manager, video_repository=video_repository)


def get_job_service(request: Request) -> JobService:
    job_service = getattr(request.app.state, "job_service", None)
    if job_service is None:
        raise RuntimeError("Job service is not initialised")
    return job_service


def get_ai_orchestrator(request: Request) -> AIOrchestrator:
    orchestrator = getattr(request.app.state, "ai_orchestrator", None)
    if orchestrator is None:
        raise RuntimeError("AI orchestrator is not initialised")
    return orchestrator


def get_provider_repository(request: Request) -> ProviderConfigRepository:
    repository = getattr(request.app.state, "provider_repository", None)
    if repository is None:
        raise RuntimeError("Provider repository is not initialised")
    return repository
