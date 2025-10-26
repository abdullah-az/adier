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
    openai_vision_model: str = Field(default="gpt-4o-mini", alias="OPENAI_VISION_MODEL")
    openai_text_model: str = Field(default="gpt-4o-mini", alias="OPENAI_TEXT_MODEL")
    openai_transcription_model: str = Field(default="gpt-4o-mini-transcribe", alias="OPENAI_TRANSCRIPTION_MODEL")
    
    # Google Gemini
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    gemini_vision_model: str = Field(default="gemini-1.5-flash", alias="GEMINI_VISION_MODEL")
    gemini_text_model: str = Field(default="gemini-1.5-pro", alias="GEMINI_TEXT_MODEL")
    
    # Anthropic Claude
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    claude_model: str = Field(default="claude-3-5-sonnet-20241022", alias="CLAUDE_MODEL")
    
    # Groq Whisper
    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    groq_whisper_model: str = Field(default="whisper-large-v3", alias="GROQ_WHISPER_MODEL")
    
    # AI orchestration
    ai_provider_priority: str = Field(default="openai,gemini,claude,groq,local", alias="AI_PROVIDER_PRIORITY")
    ai_cost_currency: str = Field(default="USD", alias="AI_COST_CURRENCY")
    ai_rate_limit_per_minute: int = Field(default=60, alias="AI_RATE_LIMIT_PER_MINUTE")
    
    # Storage
    storage_path: str = Field(default="./storage", alias="STORAGE_PATH")
    upload_max_size: int = Field(default=100 * 1024 * 1024, alias="UPLOAD_MAX_SIZE")  # 100MB
    
    # Video Processing
    ffmpeg_threads: int = Field(default=2, alias="FFMPEG_THREADS")
    video_output_format: str = Field(default="mp4", alias="VIDEO_OUTPUT_FORMAT")
    
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
