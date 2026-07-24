from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base

_engine = None
_SessionLocal = None


def _get_engine():
    global _engine
    if _engine is None:
        from app.core.config import get_settings

        settings = get_settings()
        _engine = create_engine(settings.database_url)
    return _engine


def _get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_get_engine())
    return _SessionLocal


def init_db():
    Base.metadata.create_all(bind=_get_engine())


def get_db() -> Iterator[Session]:
    db = _get_session_local()()
    try:
        yield db
    finally:
        db.close()
