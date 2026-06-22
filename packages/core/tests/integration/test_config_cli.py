from pathlib import Path

import pytest
from typer.testing import CliRunner

from ai_mini_box.cli import app as cli_app


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def cfg(tmp_path: Path) -> Path:
    return tmp_path / "config.json"


def test_config_show_smoke(runner, cfg):
    result = runner.invoke(cli_app, ["config", "show", "--config", str(cfg)])
    assert result.exit_code == 0
    assert "telegram_token" in result.output


def test_config_set_and_show(runner, cfg):
    result = runner.invoke(cli_app, ["config", "set", "poll_interval", "60", "--config", str(cfg)])
    assert result.exit_code == 0
    assert "Updated" in result.output
    result = runner.invoke(cli_app, ["config", "show", "--config", str(cfg)])
    assert "60" in result.output


def test_config_set_sensitive_masked_in_output(runner, cfg):
    result = runner.invoke(cli_app, ["config", "set", "telegram_token", "test:token", "--config", str(cfg)])
    assert result.exit_code == 0
    assert "***" in result.output
    assert "test:token" not in result.output


def test_config_set_invalid_type(runner, cfg):
    result = runner.invoke(cli_app, ["config", "set", "poll_interval", "abc", "--config", str(cfg)])
    assert result.exit_code == 1
    assert "must be an integer" in result.output


def test_config_set_unknown_key(runner, cfg):
    result = runner.invoke(cli_app, ["config", "set", "nonexistent", "value", "--config", str(cfg)])
    assert result.exit_code == 1
    assert "Unknown" in result.output


def test_config_unset(runner, cfg):
    runner.invoke(cli_app, ["config", "set", "email_imap_server", "custom.com", "--config", str(cfg)])
    result = runner.invoke(cli_app, ["config", "unset", "email_imap_server", "--config", str(cfg)])
    assert result.exit_code == 0
    assert "Reset" in result.output


def test_config_unset_already_default(runner, cfg):
    result = runner.invoke(cli_app, ["config", "unset", "email_imap_server", "--config", str(cfg)])
    assert result.exit_code == 0
    assert "already at default" in result.output


def test_config_show_sections(runner, cfg):
    result = runner.invoke(cli_app, ["config", "show", "--config", str(cfg)])
    assert "[Telegram]" in result.output
    assert "[Email]" in result.output
    assert "[General]" in result.output


def test_config_show_masks_sensitive(runner, cfg):
    runner.invoke(cli_app, ["config", "set", "telegram_token", "long-secret-token-here", "--config", str(cfg)])
    result = runner.invoke(cli_app, ["config", "show", "--config", str(cfg)])
    assert "long-secret-token-here" not in result.output
    assert "***" in result.output


def test_config_set_then_unset_shows_default(runner, cfg):
    runner.invoke(cli_app, ["config", "set", "poll_interval", "42", "--config", str(cfg)])
    result = runner.invoke(cli_app, ["config", "show", "--config", str(cfg)])
    assert "poll_interval = 42" in result.output

    runner.invoke(cli_app, ["config", "unset", "poll_interval", "--config", str(cfg)])
    result = runner.invoke(cli_app, ["config", "show", "--config", str(cfg)])
    assert "poll_interval = 42" not in result.output
    assert "poll_interval = 30" in result.output
