from __future__ import annotations

from functools import lru_cache
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Base class for all database models."""


@lru_cache
def get_database_url() -> str:
    settings = get_settings()
    return settings.database_url


def _normalize_async_url(url: str) -> str:
    if url.startswith("sqlite") and "+aiosqlite" not in url:
        return url.replace("sqlite://", "sqlite+aiosqlite://")
    return url


def _normalize_sync_url(url: str) -> str:
    if url.startswith("sqlite+aiosqlite"):
        return url.replace("sqlite+aiosqlite://", "sqlite://")
    return url


@lru_cache
def get_async_engine():
    url = _normalize_async_url(get_database_url())
    settings = get_settings()
    return create_async_engine(url, echo=settings.debug, future=True)


@lru_cache
def get_sync_engine():
    url = _normalize_sync_url(get_database_url())
    settings = get_settings()
    return create_engine(url, echo=settings.debug, future=True)


@lru_cache
def get_async_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=get_async_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for providing an async database session."""

    async_session_factory = get_async_sessionmaker()
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()


async def init_db():
    """Initialize database tables using the ORM metadata."""

    async with get_async_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
