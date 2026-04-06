from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def init_db(database_url: str | None = None) -> Engine:
    global _engine, _session_factory
    settings = get_settings()
    resolved_database_url = database_url or settings.database_url
    connect_args = {"check_same_thread": False} if resolved_database_url.startswith("sqlite") else {}
    _engine = create_engine(
        resolved_database_url,
        future=True,
        pool_pre_ping=True,
        connect_args=connect_args,
    )
    _session_factory = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    return _engine


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = init_db()
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        init_db()
    assert _session_factory is not None
    return _session_factory


def get_db() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
