from pathlib import Path

import pytest
from typer.testing import CliRunner

from ai_mini_box.cli import app
from ai_mini_box.infrastructure.config import JsonConfigManager
from ai_mini_box.infrastructure.database import Base, init_db, get_db, get_engine
from ai_mini_box.infrastructure.repositories import SqliteMessageRepo


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def tmp_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "config.json"
    config_path.write_text("{}")
    mgr = JsonConfigManager(str(config_path))
    mgr.set("telegram_token", "test:token")
    mgr.set("telegram_allowed_chat_ids", "[]")
    mgr.set("poll_interval", "30")
    return config_path


@pytest.fixture(autouse=True)
def setup_db(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    Base.metadata.create_all(get_engine())
    monkeypatch.setattr("ai_mini_box.infrastructure.database.get_db_path", lambda: db_path)
    yield
    from ai_mini_box.infrastructure.database import dispose_engine
    dispose_engine()


class FakeBot:
    def __init__(self, token: str = "test:token"):
        self.token = token

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
        JsonConfigManager(str(tmp_config)).set("telegram_token", "")
        monkeypatch.setattr(
            "ai_mini_box_telegram.commands.JsonConfigManager",
            lambda: JsonConfigManager(str(tmp_config)),
        )

        result = cli_runner.invoke(app, ["telegram", "poll"])

        assert result.exit_code == 1
        assert "telegram_token not set" in result.output

    def test_poll_respects_allowed_chat_ids(self, cli_runner, tmp_config, monkeypatch):
        JsonConfigManager(str(tmp_config)).set("telegram_allowed_chat_ids", "[123]")
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


class TestDaemonCommand:
    def test_daemon_polls_and_stops_on_interrupt(self, cli_runner, tmp_config, monkeypatch):
        monkeypatch.setattr(
            "ai_mini_box_telegram.commands.JsonConfigManager",
            lambda: JsonConfigManager(str(tmp_config)),
        )
        monkeypatch.setattr(
            "ai_mini_box_telegram.commands.TelegramBot",
            lambda token: FakeBot(),
        )
        sleep_called = False

        def _fake_sleep(*_):
            nonlocal sleep_called
            sleep_called = True
            raise KeyboardInterrupt()

        monkeypatch.setattr("ai_mini_box_telegram.commands.time.sleep", _fake_sleep)

        result = cli_runner.invoke(app, ["telegram", "daemon"])

        assert result.exit_code == 0
        assert sleep_called

    def test_daemon_handles_missing_token(self, cli_runner, tmp_config, monkeypatch):
        JsonConfigManager(str(tmp_config)).set("telegram_token", "")
        monkeypatch.setattr(
            "ai_mini_box_telegram.commands.JsonConfigManager",
            lambda: JsonConfigManager(str(tmp_config)),
        )

        def _fake_sleep(*_):
            raise KeyboardInterrupt()

        monkeypatch.setattr("ai_mini_box_telegram.commands.time.sleep", _fake_sleep)

        result = cli_runner.invoke(app, ["telegram", "daemon"])
        assert result.exit_code == 0


class TestDaemonSignalHandling:
    def test_daemon_registers_signal_handlers(self, cli_runner, tmp_config, monkeypatch):
        """Daemon must register SIGINT and SIGTERM handlers."""
        import signal as sigmod

        handlers = {}
        call_count = 0

        def _fake_signal(signum, handler):
            nonlocal call_count
            call_count += 1
            handlers[signum] = handler
            if call_count >= 2:
                raise KeyboardInterrupt()

        monkeypatch.setattr("ai_mini_box_telegram.commands.signal.signal", _fake_signal)
        monkeypatch.setattr(
            "ai_mini_box_telegram.commands.JsonConfigManager",
            lambda: JsonConfigManager(str(tmp_config)),
        )
        monkeypatch.setattr(
            "ai_mini_box_telegram.commands.TelegramBot",
            lambda token: FakeBot(),
        )
        monkeypatch.setattr("ai_mini_box_telegram.commands.time.sleep", lambda _: None)

        result = cli_runner.invoke(app, ["telegram", "daemon"])
        assert result.exit_code in (0, 130), f"Unexpected exit code: {result.exit_code}"
        assert sigmod.SIGINT in handlers
        assert sigmod.SIGTERM in handlers

    def test_daemon_works_with_closed_stdin(self, cli_runner, tmp_config, monkeypatch):
        """Simulate subprocess context — closed stdin like when launched via Popen."""
        monkeypatch.setattr(
            "ai_mini_box_telegram.commands.JsonConfigManager",
            lambda: JsonConfigManager(str(tmp_config)),
        )
        monkeypatch.setattr(
            "ai_mini_box_telegram.commands.TelegramBot",
            lambda token: FakeBot(),
        )
        monkeypatch.setattr(
            "ai_mini_box_telegram.commands.TelegramPluginConfig",
            lambda: type("MockCfg", (), {"poll_interval": 1})(),
        )

        sleep_calls = []

        def _fake_sleep(*_):
            sleep_calls.append(True)
            if len(sleep_calls) >= 2:
                raise KeyboardInterrupt()

        monkeypatch.setattr("ai_mini_box_telegram.commands.time.sleep", _fake_sleep)

        # Simulate closed stdin
        import io
        monkeypatch.setattr("sys.stdin", io.StringIO())

        result = cli_runner.invoke(app, ["telegram", "daemon"])
        assert result.exit_code == 0
        assert len(sleep_calls) == 2

    def test_daemon_handles_config_token_change(self, cli_runner, tmp_config, monkeypatch):
        """Daemon must re-read token on each loop iteration."""
        monkeypatch.setattr(
            "ai_mini_box_telegram.commands.JsonConfigManager",
            lambda: JsonConfigManager(str(tmp_config)),
        )
        monkeypatch.setattr(
            "ai_mini_box_telegram.commands.TelegramPluginConfig",
            lambda: type("MockCfg", (), {"poll_interval": 1})(),
        )

        bots_created = []

        def _bot_factory(token):
            bots_created.append(token)
            return FakeBot()

        monkeypatch.setattr("ai_mini_box_telegram.commands.TelegramBot", _bot_factory)

        calls = []

        def _fake_sleep(*_):
            calls.append(True)
            if len(calls) == 1:
                JsonConfigManager(str(tmp_config)).set("telegram_token", "new:token")
            else:
                raise KeyboardInterrupt()

        monkeypatch.setattr("ai_mini_box_telegram.commands.time.sleep", _fake_sleep)

        result = cli_runner.invoke(app, ["telegram", "daemon"])
        assert result.exit_code == 0
        assert "test:token" in bots_created
        assert "new:token" in bots_created


class TestRegistration:
    def test_telegram_shows_in_help(self, cli_runner):
        result = cli_runner.invoke(app, ["--help"])
        assert "telegram" in result.output
