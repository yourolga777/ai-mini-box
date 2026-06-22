import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ai_mini_box.infrastructure.database import Base


@pytest.fixture(scope="function")
def db_engine():
    engine = create_engine("sqlite:///:memory:")
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
