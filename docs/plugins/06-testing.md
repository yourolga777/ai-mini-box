# Testing

Use pytest with the core's testing utilities.

## Test structure

```
tests/
├── __init__.py
├── unit/
│   ├── __init__.py
│   └── test_bot.py
└── integration/
    ├── __init__.py
    └── test_commands.py
```

## Unit testing CLI commands

Use Typer's `CliRunner` to test commands:

```python
# tests/unit/test_commands.py
from typer.testing import CliRunner
from ai_mini_box.cli import app   # the main CLI app


class TestMyPlugin:
    def test_my_command(self):
        runner = CliRunner()
        result = runner.invoke(app, ["my-plugin", "list"])
        assert result.exit_code == 0
        assert "items" in result.output
```

## Integration testing with database

```python
# tests/integration/test_commands.py
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ai_mini_box.cli import app
from ai_mini_box.infrastructure.database import init_db, dispose_engine


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def setup_db(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    monkeypatch.setattr(
        "ai_mini_box.infrastructure.database.get_db_path",
        lambda: db_path,
    )
    yield
    dispose_engine()


def test_list_contacts(runner):
    result = runner.invoke(app, ["demo-list"])
    assert result.exit_code == 0
```

## Mocking config

```python
@pytest.fixture
def tmp_config(tmp_path: Path) -> Path:
    config = tmp_path / "config.json"
    config.write_text(json.dumps({
        "telegram_token": "test:token",
        "telegram_allowed_chat_ids": [],
        "poll_interval": 30,
    }))
    return config
```

## Mocking external services

Use `pytest-mock` to mock HTTP calls or other external dependencies:

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
