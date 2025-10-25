from functools import lru_cache
from typing import Optional

from pydantic import Field
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
        default="http://localhost:3000,http://localhost:5173",
        alias="CORS_ORIGINS"
    )
    
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", alias="OPENAI_MODEL")
    openai_whisper_model: str = Field(default="gpt-4o-mini-transcribe", alias="OPENAI_WHISPER_MODEL")
    openai_scene_model: str = Field(default="gpt-4o-mini", alias="OPENAI_SCENE_MODEL")
    openai_request_timeout: float = Field(default=120.0, alias="OPENAI_REQUEST_TIMEOUT")
    openai_max_retries: int = Field(default=3, alias="OPENAI_MAX_RETRIES")
    openai_retry_backoff: float = Field(default=2.0, alias="OPENAI_RETRY_BACKOFF")
    
    # Storage
    storage_path: str = Field(default="./storage", alias="STORAGE_PATH")
    upload_max_size: int = Field(default=100 * 1024 * 1024, alias="UPLOAD_MAX_SIZE")  # 100MB
    
    # Video Processing
    ffmpeg_threads: int = Field(default=2, alias="FFMPEG_THREADS")
    video_output_format: str = Field(default="mp4", alias="VIDEO_OUTPUT_FORMAT")
    
    # Transcription
    transcription_chunk_duration: float = Field(default=600.0, alias="TRANSCRIPTION_CHUNK_DURATION")
    transcription_chunk_overlap: float = Field(default=1.0, alias="TRANSCRIPTION_CHUNK_OVERLAP")
    transcription_audio_format: str = Field(default="wav", alias="TRANSCRIPTION_AUDIO_FORMAT")
    transcription_sample_rate: int = Field(default=16000, alias="TRANSCRIPTION_SAMPLE_RATE")
    transcription_channels: int = Field(default=1, alias="TRANSCRIPTION_CHANNELS")
    whisper_cli_path: Optional[str] = Field(default=None, alias="WHISPER_CPP_PATH")
    whisper_cli_model: str = Field(default="base.en", alias="WHISPER_CPP_MODEL")
    
    # Scene Detection
    scene_detection_temperature: float = Field(default=0.2, alias="SCENE_TEMPERATURE")
    scene_detection_max_scenes: int = Field(default=5, alias="SCENE_MAX_SCENES")
    scene_detection_transcript_char_limit: int = Field(default=12000, alias="SCENE_TRANSCRIPT_CHAR_LIMIT")
    scene_detection_min_confidence: float = Field(default=0.35, alias="SCENE_MIN_CONFIDENCE")
    
    # AI Prompt configuration
    ai_prompts_path: str = Field(default="./storage/metadata/ai_prompts.json", alias="AI_PROMPTS_PATH")
    
    # Database
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    
    # Workers/Concurrency
    worker_concurrency: int = Field(default=4, alias="WORKER_CONCURRENCY")
    max_queue_size: int = Field(default=100, alias="MAX_QUEUE_SIZE")
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: Optional[str] = Field(default="./logs/app.log", alias="LOG_FILE")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
