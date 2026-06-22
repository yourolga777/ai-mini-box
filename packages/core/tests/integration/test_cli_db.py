from pathlib import Path

from typer.testing import CliRunner

from ai_mini_box.cli import app


def test_db_upgrade_creates_tables(tmp_path, monkeypatch):
    db_path = tmp_path / "data" / "app.db"
    db_path.parent.mkdir(parents=True)

    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(app, ["db", "upgrade"])
    assert result.exit_code == 0
    assert "Migrations applied" in result.output
    assert db_path.exists()

    from sqlalchemy import create_engine, inspect

    engine = create_engine(f"sqlite:///{db_path}")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "contacts" in tables
    assert "products" in tables
    assert "messages" in tables
    assert "orders" in tables
