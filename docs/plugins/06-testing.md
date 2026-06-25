# Testing

Use pytest with the core's testing utilities. All models, enums and mock repositories are importable from `ai_mini_box.testing` and `ai_mini_box.core.models`.

## Test structure

```
tests/
├── __init__.py
├── unit/
│   ├── __init__.py
│   └── test_commands.py
└── integration/
    ├── __init__.py
    └── test_cli.py
```

## Unit testing with mock repositories

Use mock repos from `ai_mini_box.testing` to test your logic without a database:

```python
# tests/unit/test_commands.py
from typer.testing import CliRunner
from ai_mini_box.testing import MockContactRepo


class TestMyPlugin:
    def test_my_command(self):
        repo = MockContactRepo()
        contact = repo.add(Contact(name="Alice"))
        assert contact.id == 1
        assert repo.get_by_id(1).name == "Alice"
```

Available mocks: `MockContactRepo`, `MockProductRepo`, `MockMessageRepo`, `MockOrderRepo`, `MockKnowledgeBaseRepo`.

## Integration testing with database

Integration tests create an in-memory SQLite database with the full schema:

```python
# tests/integration/test_cli.py
import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from ai_mini_box.cli import app
from ai_mini_box.infrastructure.database import Base
from ai_mini_box.infrastructure import orm_models  # noqa: F401 — registers tables on Base


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def db_session(tmp_path):
    """In-memory SQLite with full schema, per-test isolation."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


def test_list_contacts(runner, db_session):
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
```

**Note:** Do NOT use `init_db()` in tests — use `Base.metadata.create_all(engine)` and `sessionmaker` directly. This gives you full control over the schema lifecycle.

## Mocking config

```python
@pytest.fixture
def tmp_config(tmp_path: Path) -> Path:
    import json
    config = tmp_path / "config.json"
    config.write_text(json.dumps({
        "telegram_token": "test:token",
        "telegram_allowed_chat_ids": [],
        "poll_interval": 30,
    }))
    return config
```

To override via env (useful for `AI_BOX_DB_PATH`):

```python
def test_with_env_override(monkeypatch):
    monkeypatch.setenv("AI_BOX_TELEGRAM_TOKEN", "env_token")
    from ai_mini_box.infrastructure.config import JsonConfigManager
    config = JsonConfigManager().load()
    assert config.telegram_token == "env_token"
```

## Fake class pattern (preferred for external services)

Instead of mocking individual HTTP calls, replace the **entire service class** with a test double. This is cleaner and avoids fragile `mocker.patch` chaining:

```python
class FakeBot:
    def get_updates(self, offset=None):
        return [
            {"update_id": 1, "message": {"chat": {"id": 123}, "text": "Hello"}},
        ]
    def send_message(self, chat_id, text):
        return True

def test_poll(monkeypatch):
    monkeypatch.setattr("my_plugin.bot.TelegramBot", lambda token: FakeBot())
    # ... test poll logic with FakeBot
```

Benefits: one place to mock, works for all methods, no fragile HTTP-level patching.

## Mocking external services (fallback)

Use `pytest-mock` when a fake class is impractical:

```python
def test_bot_get_updates(mocker):
    mock_resp = mocker.Mock()
    mock_resp.json.return_value = {"ok": True, "result": []}
    mock_resp.raise_for_status.return_value = None
    mocker.patch("requests.get", return_value=mock_resp)

    bot = MyBot("token")
    result = bot.get_updates()
    assert result == []
```

## Running tests

```bash
# Install your plugin with test deps
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v
```
