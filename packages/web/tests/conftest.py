import pytest
from fastapi.testclient import TestClient

from ai_mini_box.infrastructure.database import init_db, dispose_engine
from ai_mini_box_web.server import app


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    yield
    dispose_engine()


@pytest.fixture
def client(db):
    return TestClient(app)
