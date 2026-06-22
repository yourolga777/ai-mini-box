from pathlib import Path

from typer.testing import CliRunner

from ai_mini_box.cli import app


def test_init_twice_prompts(tmp_path):
    runner = CliRunner()
    db_path = tmp_path / "data" / "app.db"
    cfg_path = tmp_path / "data" / "config.json"
    db_path.parent.mkdir(parents=True)
    db_path.write_text("")
    cfg_path.write_text("{}")

    result = runner.invoke(app, ["init", "--db", str(db_path), "--config", str(cfg_path)])
    assert "already initialized" in result.output
    assert "Aborted" in result.output


def test_init_twice_confirm(tmp_path):
    runner = CliRunner()
    db_path = tmp_path / "data" / "app.db"
    cfg_path = tmp_path / "data" / "config.json"
    db_path.parent.mkdir(parents=True)
    db_path.write_text("")
    cfg_path.write_text("{}")

    result = runner.invoke(
        app, ["init", "--db", str(db_path), "--config", str(cfg_path)],
        input="y\n",
    )
    assert "Reinitialize" in result.output or "Done" in result.output


def test_init_force_skips_prompt(tmp_path):
    runner = CliRunner()
    db_path = tmp_path / "data" / "app.db"
    cfg_path = tmp_path / "data" / "config.json"
    db_path.parent.mkdir(parents=True)
    db_path.write_text("")
    cfg_path.write_text("{}")

    result = runner.invoke(
        app, ["init", "--force", "--db", str(db_path), "--config", str(cfg_path)],
    )
    assert "reinitializing" in result.output or "Done" in result.output


def test_init_partial_state_warns(tmp_path):
    runner = CliRunner()
    db_path = tmp_path / "data" / "app.db"
    cfg_path = tmp_path / "data" / "config.json"
    db_path.parent.mkdir(parents=True)
    db_path.write_text("")

    result = runner.invoke(app, ["init", "--db", str(db_path), "--config", str(cfg_path)])
    assert "partial initialization" in result.output
