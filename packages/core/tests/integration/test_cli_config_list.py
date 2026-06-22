from typer.testing import CliRunner

from ai_mini_box.cli import app


def test_config_list_shows_all_keys():
    runner = CliRunner()
    result = runner.invoke(app, ["config", "list"])
    assert result.exit_code == 0
    assert "telegram_token" in result.output
    assert "poll_interval" in result.output
    assert "email_imap_server" in result.output
    assert "email_password" in result.output


def test_config_list_shows_types():
    runner = CliRunner()
    result = runner.invoke(app, ["config", "list"])
    assert "int" in result.output
    assert "str" in result.output
    assert "bool" in result.output


def test_config_list_shows_defaults():
    runner = CliRunner()
    result = runner.invoke(app, ["config", "list"])
    assert "30" in result.output
    assert "imap.yandex.ru" in result.output
