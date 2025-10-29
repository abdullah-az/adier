from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT_DIR / "backend"
DATA_DIR = BACKEND_DIR / "data"
DEFAULT_SQLITE_PATH = DATA_DIR / "app.db"


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Core application settings
    app_name: str = Field(default="AI Video Editor Backend")
    environment: Literal["development", "production", "testing"] = Field(
        default="development", validation_alias="APP_ENV"
    )
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    log_format: Literal["json", "console"] = Field(default="console")

    # Storage paths
    storage_root: Path = Field(default=BACKEND_DIR / "storage")
    storage_temp: Path = Field(default=DATA_DIR / "tmp")
    storage_max_bytes: Optional[int] = Field(default=None)

    # Database settings
    database_url: str = Field(default=f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}")
    async_database_url: Optional[str] = None

    # Media processing limits
    max_upload_size: int = Field(default=536_870_912)

    # AI provider keys
    openai_api_key: Optional[str] = Field(default=None)
    gemini_api_key: Optional[str] = Field(default=None)
    anthropic_api_key: Optional[str] = Field(default=None)
    groq_api_key: Optional[str] = Field(default=None)

    # AI provider orchestration
    ai_provider_order: list[str] = Field(default_factory=lambda: ["openai", "gemini", "claude", "groq"])
    ai_provider_timeout_seconds: float = Field(default=30.0, ge=0.0)
    ai_provider_retries: int = Field(default=1, ge=0)
    ai_provider_retry_base_delay: float = Field(default=0.5, ge=0.0)
    ai_provider_retry_backoff_factor: float = Field(default=2.0, ge=1.0)

    # Queue settings
    queue_broker_url: str = Field(default="redis://localhost:6379/0")
    queue_result_backend: str = Field(default="redis://localhost:6379/1")
    queue_default_name: str = Field(default="ai-video-editor-jobs")

    # Accelerator configuration
    gpu_enabled: bool = Field(default=False)
    gpu_device: str = Field(default="cuda:0")

    @computed_field
    @property
    def project_root(self) -> Path:
        return ROOT_DIR

    @computed_field
    @property
    def backend_root(self) -> Path:
        return BACKEND_DIR

    @field_validator("ai_provider_order", mode="before")
    @classmethod
    def _normalise_ai_provider_order(cls, value: Any) -> list[str]:
        if value is None:
            return ["openai", "gemini", "claude", "groq"]
        if isinstance(value, str):
            items = [item.strip().lower() for item in value.split(",") if item and item.strip()]
        elif isinstance(value, (list, tuple, set)):
            items = [str(item).strip().lower() for item in value if str(item).strip()]
        else:
            raise TypeError("AI provider order must be a string or iterable of strings.")
        deduped: list[str] = []
        for item in items:
            if item not in deduped:
                deduped.append(item)
        return deduped

    def model_post_init(self, __context: dict[str, object]) -> None:
        # Resolve storage paths relative to the project root when needed
        if not self.storage_root.is_absolute():
            self.storage_root = (ROOT_DIR / self.storage_root).resolve()
        if not self.storage_temp.is_absolute():
            self.storage_temp = (ROOT_DIR / self.storage_temp).resolve()

        # Ensure storage directories exist
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.storage_temp.mkdir(parents=True, exist_ok=True)

        # Normalise database URLs and derive async variant when possible
        if self.database_url.startswith("sqlite"):
            db_path = self._ensure_sqlite_path(self.database_url)
            self.database_url = f"sqlite:///{db_path.as_posix()}"
            async_path = self._ensure_sqlite_path(self.database_url)
            self.async_database_url = f"sqlite+aiosqlite:///{async_path.as_posix()}"
        elif self.async_database_url is None:
            self.async_database_url = self._derive_async_url(self.database_url)

    @staticmethod
    def _ensure_sqlite_path(url: str) -> Path:
        """Ensure the SQLite database directory exists and return path."""
        raw_path = url.split("sqlite:///", 1)[-1]
        db_path = Path(raw_path)
        if not db_path.is_absolute():
            db_path = ROOT_DIR / raw_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return db_path

    @staticmethod
    def _derive_async_url(sync_url: str) -> Optional[str]:
        if sync_url.startswith("postgresql://"):
            return sync_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if sync_url.startswith("mysql://"):
            return sync_url.replace("mysql://", "mysql+aiomysql://", 1)
        return None


class DevelopmentSettings(Settings):
    debug: bool = True
    log_format: Literal["json", "console"] = "console"


class TestingSettings(Settings):
    environment: Literal["development", "production", "testing"] = "testing"
    debug: bool = True
    log_level: str = "DEBUG"
    database_url: str = Field(default=f"sqlite:///{(DATA_DIR / 'test.db').as_posix()}")
    log_format: Literal["json", "console"] = "console"


class ProductionSettings(Settings):
    log_format: Literal["json", "console"] = "json"


_ENVIRONMENT_CLASS_MAP = {
    "development": DevelopmentSettings,
    "dev": DevelopmentSettings,
    "testing": TestingSettings,
    "test": TestingSettings,
    "production": ProductionSettings,
    "prod": ProductionSettings,
}


@lru_cache()
def get_settings() -> Settings:
    env = os.getenv("APP_ENV", "development").lower()
    settings_cls = _ENVIRONMENT_CLASS_MAP.get(env, Settings)
    return settings_cls()
