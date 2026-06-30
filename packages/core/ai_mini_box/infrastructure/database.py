import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal = None


def get_db_url() -> str:
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url
    return f"sqlite:///{get_db_path()}"


def get_db_path() -> Path:
    env = os.environ.get("AI_BOX_DB_PATH")
    if env:
        return Path(env)
    return Path("data/app.db")


def init_db(db_path: Optional[str | Path] = None):
    global _engine, _SessionLocal
    db_path = Path(db_path) if db_path else get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    _engine = create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    event.listen(_engine, "connect", _enable_sqlite_fk)
    _SessionLocal = sessionmaker(bind=_engine)
    import ai_mini_box.infrastructure.orm_models  # noqa: F401
    Base.metadata.create_all(bind=_engine)


def _enable_sqlite_fk(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.close()


def get_engine():
    global _engine
    if _engine is None:
        init_db()
    return _engine


def get_session():
    global _SessionLocal
    if _SessionLocal is None:
        init_db()
    session = _SessionLocal()
    try:
        return session
    except Exception:
        session.close()
        raise


@contextmanager
def get_db() -> Generator[Session, None, None]:
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def dispose_engine():
    global _engine, _SessionLocal
    if _engine:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
