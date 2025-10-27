from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from app.core.config import Settings
from app.repositories.job_repository import JobRepository
from app.repositories.video_repository import VideoAssetRepository
from app.services.ai.manager import AIManager, create_ai_manager
from app.services.job_service import JobService
from app.services.video_pipeline_service import VideoPipelineService
from app.utils.storage import StorageManager
from app.workers.handlers import (
    create_export_handler,
    create_scene_detection_handler,
    create_transcription_handler,
    ingest_handler,
)
from app.workers.job_queue import JobQueue


@dataclass
class WorkerRuntime:
    job_service: JobService
    job_queue: JobQueue
    storage_manager: StorageManager
    video_repository: VideoAssetRepository
    pipeline_service: VideoPipelineService
    ai_manager: AIManager

    async def start(self) -> None:
        await self.job_queue.start()

    async def stop(self) -> None:
        await self.job_queue.stop()


def create_worker_runtime(settings: Settings) -> WorkerRuntime:
    job_repository = JobRepository(settings.storage_path)
    job_service = JobService(
        job_repository,
        default_max_attempts=settings.job_max_attempts,
        default_retry_delay=settings.job_retry_delay_seconds,
    )
    job_queue = JobQueue(
        job_service=job_service,
        concurrency=settings.worker_concurrency,
        maxsize=settings.max_queue_size,
    )

    storage_manager = StorageManager(settings.storage_path)
    video_repository = VideoAssetRepository(settings.storage_path)
    pipeline_service = VideoPipelineService(
        storage_manager=storage_manager,
        video_repository=video_repository,
        settings=settings,
    )
    ai_manager = create_ai_manager(settings)

    job_service.register_handler("ingest", ingest_handler)
    job_service.register_handler(
        "scene_detection",
        create_scene_detection_handler(ai_manager, storage_manager, video_repository),
    )
    job_service.register_handler(
        "transcription",
        create_transcription_handler(ai_manager, storage_manager, video_repository),
    )
    job_service.register_handler("export", create_export_handler(pipeline_service))

    logger.debug(
        "Configured worker runtime",
        concurrency=settings.worker_concurrency,
        max_queue_size=settings.max_queue_size,
        job_max_attempts=settings.job_max_attempts,
        job_retry_delay_seconds=settings.job_retry_delay_seconds,
    )

    return WorkerRuntime(
        job_service=job_service,
        job_queue=job_queue,
        storage_manager=storage_manager,
        video_repository=video_repository,
        pipeline_service=pipeline_service,
        ai_manager=ai_manager,
    )
