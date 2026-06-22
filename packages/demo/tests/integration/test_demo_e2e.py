from contextlib import contextmanager
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine

import ai_mini_box.infrastructure.orm_models  # noqa: F401 — register tables on Base.metadata
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

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


@pytest.fixture
def app_with_db(db_session):
    import typer
    from ai_mini_box_demo.commands import register

    @contextmanager
    def mock_get_db():
        yield db_session

    tapp = typer.Typer()
    register(tapp)

    patcher = patch("ai_mini_box_demo.commands.get_db", mock_get_db)
    patcher.start()
    yield tapp
    patcher.stop()


@pytest.fixture
def runner():
    return CliRunner()


def test_e2e_add_and_list(db_session, app_with_db, runner):
    result = runner.invoke(app_with_db, [
        "demo-add", "Иван Петров",
        "--phone", "+79991234567",
        "--email", "ivan@example.com",
    ])
    assert result.exit_code == 0
    assert "Created contact" in result.output
    assert "Иван Петров" in result.output

    result = runner.invoke(app_with_db, [
        "demo-list", "--limit", "5",
    ])
    assert result.exit_code == 0
    assert "Иван Петров" in result.output
    assert "+79991234567" in result.output


def test_e2e_get_by_id(db_session, app_with_db, runner):
    runner.invoke(app_with_db, [
        "demo-add", "Alice", "--phone", "+111",
    ])

    result = runner.invoke(app_with_db, ["demo-get", "1"])
    assert result.exit_code == 0
    assert "Alice" in result.output
    assert "+111" in result.output


def test_e2e_get_not_found(db_session, app_with_db, runner):
    result = runner.invoke(app_with_db, ["demo-get", "999"])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_e2e_list_pagination(db_session, app_with_db, runner):
    for name in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]:
        runner.invoke(app_with_db, ["demo-add", name])

    result_all = runner.invoke(app_with_db, ["demo-list", "--limit", "10"])
    assert result_all.exit_code == 0
    lines = [l for l in result_all.output.strip().split("\n") if l]
    assert len(lines) == 5

    result_page = runner.invoke(app_with_db, ["demo-list", "--limit", "2", "--offset", "0"])
    assert result_page.exit_code == 0
    page_lines = [l for l in result_page.output.strip().split("\n") if l]
    assert len(page_lines) == 2
