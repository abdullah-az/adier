from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from app.core.config import Settings
from app.repositories.job_repository import JobRepository
from app.repositories.scene_repository import SceneDetectionRepository
from app.repositories.subtitle_repository import SubtitleRepository
from app.repositories.video_repository import VideoAssetRepository
from app.services.job_service import JobService
from app.services.openai_client import OpenAIClient
from app.services.scene_analysis_service import SceneAnalysisService
from app.services.transcription_service import TranscriptionService
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
    subtitle_repository: SubtitleRepository
    scene_repository: SceneDetectionRepository
    openai_client: OpenAIClient
    transcription_service: TranscriptionService
    scene_service: SceneAnalysisService
    pipeline_service: VideoPipelineService

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
    subtitle_repository = SubtitleRepository(settings.storage_path)
    scene_repository = SceneDetectionRepository(settings.storage_path)

    openai_client = OpenAIClient(
        api_key=settings.openai_api_key,
        organization=settings.openai_organization,
        request_timeout=settings.openai_request_timeout,
        max_retries=settings.openai_max_retries,
    )

    transcription_service = TranscriptionService(
        settings=settings,
        storage_manager=storage_manager,
        video_repository=video_repository,
        subtitle_repository=subtitle_repository,
        openai_client=openai_client,
    )
    scene_service = SceneAnalysisService(
        settings=settings,
        video_repository=video_repository,
        subtitle_repository=subtitle_repository,
        scene_repository=scene_repository,
        openai_client=openai_client,
    )
    pipeline_service = VideoPipelineService(
        storage_manager=storage_manager,
        video_repository=video_repository,
        settings=settings,
    )

    job_service.register_handler("ingest", ingest_handler)
    job_service.register_handler(
        "transcription",
        create_transcription_handler(transcription_service),
    )
    job_service.register_handler(
        "scene_detection",
        create_scene_detection_handler(scene_service),
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
        subtitle_repository=subtitle_repository,
        scene_repository=scene_repository,
        openai_client=openai_client,
        transcription_service=transcription_service,
        scene_service=scene_service,
        pipeline_service=pipeline_service,
    )
