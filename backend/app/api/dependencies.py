from functools import lru_cache

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.repositories.job_repository import JobRepository
from app.repositories.video_repository import VideoAssetRepository
from app.services.ai_suggestion_service import AiSuggestionService
from app.services.job_service import JobService
from app.services.project_service import ProjectService
from app.services.storage_service import StorageService
from app.services.timeline_service import TimelineService
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


def get_project_service(request: Request) -> ProjectService:
    project_service = getattr(request.app.state, "project_service", None)
    if project_service is None:
        raise RuntimeError("Project service is not initialised")
    return project_service


def get_timeline_service(request: Request) -> TimelineService:
    timeline_service = getattr(request.app.state, "timeline_service", None)
    if timeline_service is None:
        raise RuntimeError("Timeline service is not initialised")
    return timeline_service


def get_ai_service(request: Request) -> AiSuggestionService:
    ai_service = getattr(request.app.state, "ai_service", None)
    if ai_service is None:
        raise RuntimeError("AI suggestion service is not initialised")
    return ai_service
