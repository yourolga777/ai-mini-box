from typer.testing import CliRunner

from ai_mini_box.cli import app


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "Initialize project" in result.output
