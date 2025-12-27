from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Database
    database_url: str = "sqlite:///./test.db"
    
    # Storage
    storage_path: str = "/workspace/storage"
    
    # FFmpeg
    ffmpeg_path: str = "ffmpeg"
    ffprobe_path: str = "ffprobe"


settings = Settings()