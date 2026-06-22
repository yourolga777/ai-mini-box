import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ai_mini_box.cli import app
from ai_mini_box.testing import (
    MockContactRepo,
    MockMessageRepo,
    MockOrderRepo,
    MockProductRepo,
)


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def tmp_config(tmp_path: Path) -> Path:
    config = tmp_path / "config.json"
    config.write_text(json.dumps({
        "telegram_token": "test:token",
        "email_imap_server": "imap.test.com",
        "email_login": "test@test.com",
        "email_password": "",
        "poll_interval": 30,
    }))
    return config


@pytest.fixture
def mock_contact_repo():
    return MockContactRepo()


@pytest.fixture
def mock_product_repo():
    return MockProductRepo()


@pytest.fixture
def mock_message_repo():
    return MockMessageRepo()


@pytest.fixture
def mock_order_repo():
    return MockOrderRepo()
