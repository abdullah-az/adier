from functools import lru_cache
from typing import Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = Field(default="Quiz System Backend", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    
    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://localhost:8080",
        alias="CORS_ORIGINS"
    )
    
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", alias="OPENAI_MODEL")
    openai_organization: Optional[str] = Field(default=None, alias="OPENAI_ORGANIZATION")
    openai_request_timeout: float = Field(default=60.0, alias="OPENAI_REQUEST_TIMEOUT")
    openai_max_retries: int = Field(default=3, alias="OPENAI_MAX_RETRIES")
    openai_transcription_model: str = Field(
        default="gpt-4o-mini-transcribe",
        alias="OPENAI_TRANSCRIPTION_MODEL",
    )
    openai_transcription_chunk_seconds: int = Field(
        default=900,
        alias="OPENAI_TRANSCRIPTION_CHUNK_SECONDS",
    )
    openai_transcription_sample_rate: int = Field(
        default=16000,
        alias="OPENAI_TRANSCRIPTION_SAMPLE_RATE",
    )
    openai_scene_model: str = Field(default="gpt-4o-mini", alias="OPENAI_SCENE_MODEL")
    openai_scene_max_scenes: int = Field(default=5, alias="OPENAI_SCENE_MAX_SCENES")
    
    # Storage
    storage_path: str = Field(
        default="./storage",
        alias="STORAGE_PATH",
        validation_alias=AliasChoices("STORAGE_ROOT", "STORAGE_PATH"),
    )
    upload_max_size: int = Field(default=100 * 1024 * 1024, alias="UPLOAD_MAX_SIZE")  # 100MB
    
    # Video Processing
    ffmpeg_threads: int = Field(default=2, alias="FFMPEG_THREADS")
    video_output_format: str = Field(default="mp4", alias="VIDEO_OUTPUT_FORMAT")
    
    # Database
    database_url: str = Field(
        default="sqlite:///./storage/app.db",
        alias="DATABASE_URL",
    )
    
    # Workers/Concurrency
    worker_concurrency: int = Field(default=4, alias="WORKER_CONCURRENCY")
    max_queue_size: int = Field(default=100, alias="MAX_QUEUE_SIZE")
    job_max_attempts: int = Field(default=3, alias="JOB_MAX_ATTEMPTS")
    job_retry_delay_seconds: float = Field(default=5.0, alias="JOB_RETRY_DELAY_SECONDS")
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: Optional[str] = Field(default="./logs/app.log", alias="LOG_FILE")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
