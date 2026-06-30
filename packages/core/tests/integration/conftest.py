import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from ai_mini_box.infrastructure.database import Base


def _enable_fk(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture(scope="function")
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    event.listen(engine, "connect", _enable_fk)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_engine):
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()
