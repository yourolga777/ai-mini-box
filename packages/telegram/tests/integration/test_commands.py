import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ai_mini_box.cli import app
from ai_mini_box.infrastructure.config import JsonConfigManager
from ai_mini_box.infrastructure.database import init_db, get_db
from ai_mini_box.infrastructure.repositories import SqliteMessageRepo


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def tmp_config(tmp_path: Path) -> Path:
    config = tmp_path / "config.json"
    config.write_text(json.dumps({
        "telegram_token": "test:token",
        "telegram_allowed_chat_ids": [],
        "poll_interval": 30,
    }))
    return config


@pytest.fixture(autouse=True)
def setup_db(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    monkeypatch.setattr("ai_mini_box.infrastructure.database.get_db_path", lambda: db_path)
    yield
    from ai_mini_box.infrastructure.database import dispose_engine
    dispose_engine()


class FakeBot:
    def get_updates(self, offset=None):
        return [
            {
                "update_id": 1,
                "message": {
                    "chat": {"id": 123},
                    "text": "Hello from test",
                },
            },
            {
                "update_id": 2,
                "message": {
                    "chat": {"id": 456},
                    "text": "Second message",
                },
            },
        ]


class TestPollCommand:
    def test_poll_saves_messages_and_prints_count(self, cli_runner, tmp_config, monkeypatch):
        monkeypatch.setattr(
            "ai_mini_box_telegram.commands.JsonConfigManager",
            lambda: JsonConfigManager(str(tmp_config)),
        )
        monkeypatch.setattr(
            "ai_mini_box_telegram.commands.TelegramBot",
            lambda token: FakeBot(),
        )

        result = cli_runner.invoke(app, ["telegram", "poll"])

        assert result.exit_code == 0, result.output
        assert "Processed 2 new messages" in result.output

        with get_db() as session:
            message_repo = SqliteMessageRepo(session)
            messages = message_repo.list()
            assert len(messages) == 2
            texts = {m.text for m in messages}
            assert "Hello from test" in texts
            assert "Second message" in texts

    def test_poll_shows_error_when_no_token(self, cli_runner, tmp_config, monkeypatch):
        tmp_config.write_text(json.dumps({"telegram_token": ""}))
        monkeypatch.setattr(
            "ai_mini_box_telegram.commands.JsonConfigManager",
            lambda: JsonConfigManager(str(tmp_config)),
        )

        result = cli_runner.invoke(app, ["telegram", "poll"])

        assert result.exit_code == 1
        assert "telegram_token not set" in result.output

    def test_poll_respects_allowed_chat_ids(self, cli_runner, tmp_config, monkeypatch):
        tmp_config.write_text(json.dumps({
            "telegram_token": "test:token",
            "telegram_allowed_chat_ids": [123],
            "poll_interval": 30,
        }))
        monkeypatch.setattr(
            "ai_mini_box_telegram.commands.JsonConfigManager",
            lambda: JsonConfigManager(str(tmp_config)),
        )
        monkeypatch.setattr(
            "ai_mini_box_telegram.commands.TelegramBot",
            lambda token: FakeBot(),
        )

        result = cli_runner.invoke(app, ["telegram", "poll"])

        assert result.exit_code == 0
        assert "Processed 1 new messages" in result.output

        with get_db() as session:
            message_repo = SqliteMessageRepo(session)
            messages = message_repo.list()
            assert len(messages) == 1
            assert messages[0].chat_id == "123"


class TestRegistration:
    def test_telegram_shows_in_help(self, cli_runner):
        result = cli_runner.invoke(app, ["--help"])
        assert "telegram" in result.output
