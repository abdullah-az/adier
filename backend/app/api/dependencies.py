from functools import lru_cache

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.repositories.job_repository import JobRepository
from app.repositories.scene_repository import SceneAnalysisRepository
from app.repositories.transcript_repository import TranscriptRepository
from app.repositories.video_repository import VideoAssetRepository
from app.services.job_service import JobService
from app.services.storage_service import StorageService
from app.services.prompt_service import PromptService
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
def _transcript_repository_factory(storage_path: str) -> TranscriptRepository:
    return TranscriptRepository(storage_root=storage_path)


@lru_cache
def _scene_repository_factory(storage_path: str) -> SceneAnalysisRepository:
    return SceneAnalysisRepository(storage_root=storage_path)


@lru_cache
def _prompt_service_factory(prompts_path: str) -> PromptService:
    return PromptService(config_path=prompts_path)


def get_storage_manager(settings: Settings = Depends(get_settings)) -> StorageManager:
    """Get shared StorageManager instance."""
    return _storage_manager_factory(settings.storage_path)


def get_video_repository(settings: Settings = Depends(get_settings)) -> VideoAssetRepository:
    """Get shared VideoAssetRepository instance."""
    return _video_repository_factory(settings.storage_path)


def get_job_repository(settings: Settings = Depends(get_settings)) -> JobRepository:
    """Get shared JobRepository instance."""
    return _job_repository_factory(settings.storage_path)


def get_transcript_repository(settings: Settings = Depends(get_settings)) -> TranscriptRepository:
    """Get shared TranscriptRepository instance."""
    return _transcript_repository_factory(settings.storage_path)


def get_scene_repository(settings: Settings = Depends(get_settings)) -> SceneAnalysisRepository:
    """Get shared SceneAnalysisRepository instance."""
    return _scene_repository_factory(settings.storage_path)


def get_prompt_service(settings: Settings = Depends(get_settings)) -> PromptService:
    """Get configured prompt service (supports overrides from disk)."""
    return _prompt_service_factory(settings.ai_prompts_path)


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
