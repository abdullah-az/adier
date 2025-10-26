from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.health import router as health_router
from app.api.jobs import router as jobs_router
from app.api.storage import router as storage_router
from app.api.timeline import router as timeline_router
from app.api.videos import router as videos_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.repositories.job_repository import JobRepository
from app.repositories.video_repository import VideoAssetRepository
from app.services.job_service import JobService
from app.services.video_pipeline_service import VideoPipelineService
from app.utils.storage import StorageManager
from app.workers.handlers import (
    create_export_handler,
    ingest_handler,
    scene_detection_handler,
    transcription_handler,
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
    try:
        job_repository = JobRepository(settings.storage_path)
        job_service = JobService(job_repository)
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

        job_service.register_handler("ingest", ingest_handler)
        job_service.register_handler("scene_detection", scene_detection_handler)
        job_service.register_handler("transcription", transcription_handler)
        job_service.register_handler("export", create_export_handler(pipeline_service))

        app.state.job_service = job_service
        app.state.job_queue = job_queue
        app.state.pipeline_service = pipeline_service
        app.state.storage_manager = storage_manager
        app.state.video_repository = video_repository

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
    app.include_router(timeline_router)
    app.include_router(jobs_router)
    
    return app


app = create_app()
