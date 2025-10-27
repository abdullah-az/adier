from functools import lru_cache

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.repositories.job_repository import JobRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.video_repository import VideoAssetRepository
from app.services.ai_service import AISuggestionService
from app.services.job_service import JobService
from app.services.project_service import ProjectService
from app.services.storage_service import StorageService
from app.services.video_pipeline_service import VideoPipelineService
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


@lru_cache
def _project_repository_factory(storage_path: str) -> ProjectRepository:
    return ProjectRepository(storage_root=storage_path)


@lru_cache
def _project_service_factory(storage_path: str) -> ProjectService:
    return ProjectService(
        repository=_project_repository_factory(storage_path),
        storage_manager=_storage_manager_factory(storage_path),
        video_repository=_video_repository_factory(storage_path),
    )


@lru_cache
def _ai_suggestion_service_factory(storage_path: str) -> AISuggestionService:
    return AISuggestionService(_video_repository_factory(storage_path))


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


def get_project_repository(settings: Settings = Depends(get_settings)) -> ProjectRepository:
    return _project_repository_factory(settings.storage_path)


def get_project_service(settings: Settings = Depends(get_settings)) -> ProjectService:
    return _project_service_factory(settings.storage_path)


def get_ai_suggestion_service(settings: Settings = Depends(get_settings)) -> AISuggestionService:
    return _ai_suggestion_service_factory(settings.storage_path)


def get_pipeline_service(request: Request) -> VideoPipelineService:
    pipeline = getattr(request.app.state, "pipeline_service", None)
    if pipeline is None:
        raise RuntimeError("Pipeline service is not initialised")
    return pipeline


def get_job_service(request: Request) -> JobService:
    job_service = getattr(request.app.state, "job_service", None)
    if job_service is None:
        raise RuntimeError("Job service is not initialised")
    return job_service
