from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Generator, Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL, make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


settings = get_settings()
DATABASE_URL = settings.database_url


def _resolve_sqlite_path(url: URL) -> Path:
    if url.database is None:
        raise ValueError("SQLite URL must include a database path")

    db_path = Path(url.database)
    if not db_path.is_absolute():
        project_root = Path(__file__).resolve().parents[2]
        db_path = project_root / db_path
    return db_path


def _create_engine(database_url: str) -> Engine:
    url = make_url(database_url)
    connect_args: dict[str, object] = {}

    if url.get_backend_name() == "sqlite":
        connect_args["check_same_thread"] = False
        if url.database not in (None, ":memory:"):
            db_path = _resolve_sqlite_path(url)
            db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(database_url, connect_args=connect_args, future=True)


engine = _create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
SessionFactory = Callable[[], Session]


@contextmanager
def session_scope(session_factory: SessionFactory = SessionLocal) -> Iterator[Session]:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
