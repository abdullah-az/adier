from __future__ import annotations

from contextlib import contextmanager
from typing import AsyncGenerator, Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import Settings, get_settings


def _get_connect_args(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


settings: Settings = get_settings()


def _create_engine(url: str) -> Engine:
    connect_args = _get_connect_args(url)
    return create_engine(url, connect_args=connect_args, future=True)


def _create_async_engine(url: str) -> AsyncEngine:
    return create_async_engine(url, future=True)


engine: Engine = _create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)

_async_engine: Optional[AsyncEngine] = None
AsyncSessionLocal: Optional[sessionmaker] = None

if settings.async_database_url:
    _async_engine = _create_async_engine(settings.async_database_url)
    AsyncSessionLocal = sessionmaker(
        bind=_async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""

    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    if AsyncSessionLocal is None:
        raise RuntimeError("Async database session requested but async engine is not configured.")

    async with AsyncSessionLocal() as session:  # type: ignore[misc]
        yield session


__all__ = [
    "engine",
    "SessionLocal",
    "AsyncSessionLocal",
    "session_scope",
    "get_db",
    "get_async_db",
    "settings",
]
