import importlib.metadata
import os
from pathlib import Path
from typing import Any

import typer

from ai_mini_box.infrastructure.database import get_db, init_db

app = typer.Typer(
    name="ai-mini-box",
    help="AI mini box — automation of small business",
    no_args_is_help=True,
    pretty_exceptions_short=os.environ.get("AI_BOX_VERBOSE") != "1",
)


@app.callback()
def main_callback(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    log_file: str = typer.Option(None, "--log-file", help="Path to log file"),
):
    if verbose:
        os.environ["AI_BOX_VERBOSE"] = "1"
    from ai_mini_box.infrastructure.logger import setup_logging

    setup_logging(verbose=verbose, log_file=Path(log_file) if log_file else None)


config_app = typer.Typer(help="Manage configuration")
app.add_typer(config_app, name="config")

db_app = typer.Typer(help="Database management")
app.add_typer(db_app, name="db")


@app.command()
def init(
    force: bool = typer.Option(False, "--force", help="Overwrite existing config"),
    config_path: str = typer.Option("data/config.json", "--config", help="Config path"),
    db_path: str = typer.Option("data/app.db", "--db", help="Database path"),
):
    """Initialize project: create config, database, directories."""
    from ai_mini_box.infrastructure.config import JsonConfigManager

    cfg_exists = Path(config_path).exists()
    db_exists = Path(db_path).exists()

    if cfg_exists and db_exists:
        if force:
            typer.echo("Warning: reinitializing (--force).")
        else:
            typer.echo("Warning: project already initialized.")
            typer.echo(f"  Config: {config_path}")
            typer.echo(f"  DB:     {db_path}")
            if not typer.confirm("Reinitialize? This will reset the config.", default=False):
                typer.echo("Aborted.")
                raise typer.Exit(code=0)
    elif cfg_exists or db_exists:
        typer.echo("Warning: partial initialization detected (config or DB exists).")

    dirs = [Path("data"), Path("data/backup"), Path("data/models"), Path("data/training")]
    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True)
            typer.echo(f"  Created: {d}")

    cfg_path = Path(config_path)
    if not cfg_path.exists() or force:
        manager = JsonConfigManager(cfg_path)
        manager.save(manager.load())
        typer.echo(f"  Created: {cfg_path}" + (" (overwritten)" if force else ""))

    if not Path(db_path).exists() or force:
        init_db(db_path)
        typer.echo(f"  Created: {db_path}")
        _run_migrations(Path(db_path))
        typer.echo("  Migrations applied.")

    typer.echo("Done.")


@app.command()
def check_db():
    """Check database connection and schema."""
    try:
        from sqlalchemy import text

        with get_db() as session:
            result = session.execute(text("SELECT 1"))
            val = result.scalar()
            if val == 1:
                typer.echo("  Database: connected")
            from ai_mini_box.infrastructure.database import Base

            tables = list(Base.metadata.tables.keys())
            typer.echo(f"  Tables: {', '.join(tables) if tables else 'none'}")
    except Exception as e:
        typer.echo(f"  Database: ERROR - {e}")
        raise typer.Exit(code=1)


def _get_migrations_dir() -> Path:
    import ai_mini_box

    package_dir = Path(ai_mini_box.__file__).parent
    for candidate in (package_dir / "migrations", package_dir.parent / "migrations"):
        if candidate.exists():
            return candidate
    raise FileNotFoundError("migrations directory not found — reinstall the package")


def _run_migrations(db_path: Path | None = None):
    try:
        from alembic.config import Config
        from alembic import command
    except ImportError:
        typer.echo("Error: alembic not installed. Run: pip install alembic")
        raise typer.Exit(code=1)

    try:
        migrations_dir = _get_migrations_dir()
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)

    db_path = db_path.resolve() if db_path else Path("data/app.db").resolve()
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", str(migrations_dir))
    alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    command.upgrade(alembic_cfg, "head")


@db_app.command()
def upgrade():
    """Apply database migrations."""
    _run_migrations()
    typer.echo("  Migrations applied.")


@config_app.command(name="list")
def config_list():
    """List all available config keys with types and defaults."""
    from ai_mini_box.infrastructure.config import AppConfig

    for key, field in AppConfig.model_fields.items():
        annotation = field.annotation
        type_str = getattr(annotation, "__name__", str(annotation))
        default = field.default if field.default is not None else field.default_factory()
        typer.echo(f"  {key} ({type_str}) = {default!r}")


@config_app.command(name="show")
def config_show(
    config_path: str = typer.Option("data/config.json", "--config", help="Config path"),
):
    """Show current configuration grouped by sections."""
    from ai_mini_box.infrastructure.config import AppConfig, JsonConfigManager, SENSITIVE_FIELDS

    manager = JsonConfigManager(config_path)
    config = manager.load()

    env_overrides = _detect_env_overrides(config)

    groups: dict[str, list[tuple[str, Any, bool]]] = {}
    for key in AppConfig.model_fields:
        section = AppConfig.guess_section(key)
        value = getattr(config, key)
        is_env = key in env_overrides
        masked = _mask_value(key, str(value)) if key in SENSITIVE_FIELDS and value else str(value)
        groups.setdefault(section, []).append((key, masked, is_env))

    for section in sorted(groups, key=_section_order):
        typer.echo(typer.style(f"[{section}]", bold=True, fg=typer.colors.CYAN))
        for key, value, is_env in groups[section]:
            suffix = typer.style(" (env)", dim=True, fg=typer.colors.YELLOW) if is_env else ""
            typer.echo(f"  {key} = {value}{suffix}")


@config_app.command(name="set")
def config_set(
    key: str = typer.Argument(..., help="Config key"),
    value: str = typer.Argument(..., help="Config value"),
    config_path: str = typer.Option("data/config.json", "--config", help="Config path"),
):
    """Set a config value."""
    from ai_mini_box.infrastructure.config import JsonConfigManager, SENSITIVE_FIELDS

    manager = JsonConfigManager(config_path)
    try:
        manager.set(key, value)
    except ValueError as e:
        typer.echo(typer.style(f"Error: {e}", fg=typer.colors.RED))
        raise typer.Exit(code=1)

    label = f"{key} = {value}"
    if key in SENSITIVE_FIELDS:
        label = f"{key} = ***"
    typer.echo(typer.style(f"  Updated: {label}", fg=typer.colors.GREEN))


@config_app.command(name="unset")
def config_unset(
    key: str = typer.Argument(..., help="Config key to reset to default"),
    config_path: str = typer.Option("data/config.json", "--config", help="Config path"),
):
    """Reset a config key to its default value."""
    from ai_mini_box.infrastructure.config import JsonConfigManager

    manager = JsonConfigManager(config_path)
    try:
        changed = manager.unset(key)
    except ValueError as e:
        typer.echo(typer.style(f"Error: {e}", fg=typer.colors.RED))
        raise typer.Exit(code=1)

    if changed:
        typer.echo(typer.style(f"  Reset: {key} to default", fg=typer.colors.GREEN))
    else:
        typer.echo(f"  {key} already at default")


def _mask_value(key: str, value: str) -> str:
    if len(value) <= 4:
        return "****"
    return value[:2] + "*" * (len(value) - 5) + value[-3:]


def _detect_env_overrides(config) -> set[str]:
    from ai_mini_box.infrastructure.config import AppConfig

    overrides = set()
    prefix = "AI_BOX_"
    for field_name in AppConfig.model_fields:
        env_key = f"{prefix}{field_name.upper()}"
        if os.environ.get(env_key) is not None:
            overrides.add(field_name)
    return overrides


_SECTION_ORDER = {
    "Telegram": 1, "Email": 2, "LLM": 3, "Schedule": 4,
    "WhatsApp": 5, "Notifications": 6, "SMS": 7,
    "YooKassa": 8, "Tinkoff": 9, "Sber": 10, "General": 11,
}


def _section_order(s: str) -> int:
    return _SECTION_ORDER.get(s, 99)


for ep in importlib.metadata.entry_points(group="ai_mini_box.tools"):
    try:
        register_func = ep.load()
        if callable(register_func):
            register_func(app)
    except Exception as e:
        typer.echo(f"Warning: failed to load tool {ep.name}: {e}", err=True)
