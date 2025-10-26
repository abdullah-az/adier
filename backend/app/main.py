from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.health import router as health_router
from app.api.jobs import router as jobs_router
from app.api.providers import router as providers_router
from app.api.storage import router as storage_router
from app.api.videos import router as videos_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.repositories.job_repository import JobRepository
from app.repositories.provider_repository import ProviderConfigRepository
from app.repositories.video_repository import VideoAssetRepository
from app.services.ai import (
    AIOrchestrator,
    ClaudeProvider,
    GeminiProvider,
    GroqProvider,
    LocalFallbackProvider,
    OpenAIProvider,
)
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"OpenAI API configured: {bool(settings.openai_api_key)}")
    logger.info(f"Gemini API configured: {bool(settings.gemini_api_key)}")
    logger.info(f"Claude API configured: {bool(settings.anthropic_api_key)}")
    logger.info(f"Groq API configured: {bool(settings.groq_api_key)}")

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

        provider_repository = ProviderConfigRepository(settings.storage_path)
        providers = [
            OpenAIProvider(
                api_key=settings.openai_api_key,
                vision_model=settings.openai_vision_model,
                text_model=settings.openai_text_model,
                transcription_model=settings.openai_transcription_model,
                cost_currency=settings.ai_cost_currency,
            ),
            GeminiProvider(
                api_key=settings.gemini_api_key,
                vision_model=settings.gemini_vision_model,
                text_model=settings.gemini_text_model,
                cost_currency=settings.ai_cost_currency,
            ),
            ClaudeProvider(
                api_key=settings.anthropic_api_key,
                model=settings.claude_model,
                cost_currency=settings.ai_cost_currency,
            ),
            GroqProvider(
                api_key=settings.groq_api_key,
                whisper_model=settings.groq_whisper_model,
                cost_currency=settings.ai_cost_currency,
            ),
        ]
        ai_orchestrator = await AIOrchestrator.create(
            settings,
            provider_repository,
            providers=providers,
            fallback_provider=LocalFallbackProvider(),
        )

        job_service.register_handler("ingest", ingest_handler)
        job_service.register_handler("scene_detection", create_scene_detection_handler(ai_orchestrator))
        job_service.register_handler("transcription", create_transcription_handler(ai_orchestrator))
        job_service.register_handler("export", create_export_handler(pipeline_service))

        app.state.job_service = job_service
        app.state.job_queue = job_queue
        app.state.pipeline_service = pipeline_service
        app.state.storage_manager = storage_manager
        app.state.video_repository = video_repository
        app.state.provider_repository = provider_repository
        app.state.ai_orchestrator = ai_orchestrator

        all_providers = ai_orchestrator.list_providers()
        available_count = sum(1 for entry in all_providers if entry.get("available"))
        configured_count = sum(1 for entry in all_providers if entry.get("configured"))
        logger.info(
            "AI providers initialised",
            total=len(all_providers),
            configured=configured_count,
            available=available_count,
        )

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
    app.include_router(providers_router)
    app.include_router(storage_router)
    app.include_router(videos_router)
    app.include_router(jobs_router)
    
    return app


app = create_app()
