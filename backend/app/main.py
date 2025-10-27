from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.health import router as health_router
from app.api.jobs import router as jobs_router
from app.api.providers import router as ai_router
from app.api.storage import router as storage_router
from app.api.videos import router as videos_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.workers.runtime import WorkerRuntime, create_worker_runtime


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")

    runtime: WorkerRuntime | None = None
    try:
        runtime = create_worker_runtime(settings)

        app.state.worker_runtime = runtime
        app.state.job_service = runtime.job_service
        app.state.job_queue = runtime.job_queue
        app.state.pipeline_service = runtime.pipeline_service
        app.state.storage_manager = runtime.storage_manager
        app.state.video_repository = runtime.video_repository
        app.state.ai_manager = runtime.ai_manager

        logger.info(
            "Initialised background job queue",
            concurrency=settings.worker_concurrency,
            max_queue_size=settings.max_queue_size,
            max_attempts=settings.job_max_attempts,
            retry_delay_seconds=settings.job_retry_delay_seconds,
        )
        logger.info(
            "AI providers configured",
            providers=list(runtime.ai_manager.list_registered_providers()),
        )

        await runtime.start()
        yield
    finally:
        if runtime is not None:
            await runtime.stop()
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
    app.include_router(ai_router)
    app.include_router(jobs_router)
    
    return app


app = create_app()
