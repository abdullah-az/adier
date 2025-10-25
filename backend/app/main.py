from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.health import router as health_router
from app.api.jobs import router as jobs_router
from app.api.storage import router as storage_router
from app.api.videos import router as videos_router
from app.api.ai import router as ai_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.repositories.job_repository import JobRepository
from app.repositories.scene_repository import SceneAnalysisRepository
from app.repositories.transcript_repository import TranscriptRepository
from app.repositories.video_repository import VideoAssetRepository
from app.services.job_service import JobService
from app.services.openai_service import OpenAIService
from app.services.prompt_service import PromptService
from app.services.scene_detection_service import SceneDetectionService
from app.services.transcription_service import TranscriptionService
from app.utils.storage import StorageManager
from app.workers.handlers import (
    create_scene_detection_handler,
    create_transcription_handler,
    export_handler,
    ingest_handler,
)
from app.workers.job_queue import JobQueue


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"OpenAI API configured: {bool(settings.openai_api_key)}")

    job_queue: JobQueue | None = None
    openai_service: OpenAIService | None = None
    try:
        storage_manager = StorageManager(settings.storage_path)
        video_repository = VideoAssetRepository(settings.storage_path)
        transcript_repository = TranscriptRepository(settings.storage_path)
        scene_repository = SceneAnalysisRepository(settings.storage_path)
        prompt_service = PromptService(settings.ai_prompts_path)
        openai_service = OpenAIService(
            api_key=settings.openai_api_key,
            request_timeout=settings.openai_request_timeout,
            max_retries=settings.openai_max_retries,
            backoff_seconds=settings.openai_retry_backoff,
        )

        job_repository = JobRepository(settings.storage_path)
        job_service = JobService(job_repository)
        job_queue = JobQueue(
            job_service=job_service,
            concurrency=settings.worker_concurrency,
            maxsize=settings.max_queue_size,
        )

        transcription_service = TranscriptionService(
            settings=settings,
            storage_manager=storage_manager,
            video_repository=video_repository,
            transcript_repository=transcript_repository,
            openai_service=openai_service,
        )
        scene_detection_service = SceneDetectionService(
            settings=settings,
            video_repository=video_repository,
            transcript_repository=transcript_repository,
            scene_repository=scene_repository,
            prompt_service=prompt_service,
            openai_service=openai_service,
        )

        job_service.register_handler("ingest", ingest_handler)
        job_service.register_handler("scene_detection", create_scene_detection_handler(scene_detection_service))
        job_service.register_handler("transcription", create_transcription_handler(transcription_service))
        job_service.register_handler("export", export_handler)

        app.state.job_service = job_service
        app.state.job_queue = job_queue
        app.state.storage_manager = storage_manager
        app.state.video_repository = video_repository
        app.state.transcript_repository = transcript_repository
        app.state.scene_repository = scene_repository
        app.state.prompt_service = prompt_service
        app.state.openai_service = openai_service
        app.state.transcription_service = transcription_service
        app.state.scene_detection_service = scene_detection_service

        logger.info(
            "Initialised background job queue",
            concurrency=settings.worker_concurrency,
            max_queue_size=settings.max_queue_size,
        )

        await job_queue.start()
        yield
    finally:
        if job_queue is not None:
            await job_queue.stop()
        if openai_service is not None:
            await openai_service.aclose()
        logger.info("Shutting down application")


def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health_router)
    app.include_router(storage_router)
    app.include_router(videos_router)
    app.include_router(jobs_router)
    app.include_router(ai_router)
    
    return app


app = create_app()
