# CLI Entry Point

Every plugin must expose a `register(app: typer.Typer)` function. This is the bridge between your plugin and the core CLI.

## Simple example

```python
# ai_mini_box_my_plugin/commands.py
import typer


def register(app: typer.Typer):
    @app.command(name="my-plugin-list")
    def list_items(
        limit: int = typer.Option(10, "--limit", "-n", help="Max results"),
    ):
        """List items from my plugin."""
        typer.echo(f"Listing up to {limit} items...")
```

## Adding a subcommand group

```python
# ai_mini_box_my_plugin/commands.py
import typer


def register(app: typer.Typer):
    # Create a sub-typer for your plugin
    my_plugin = typer.Typer(help="My plugin commands")
    app.add_typer(my_plugin, name="my-plugin")

    @my_plugin.command()
    def list(
        limit: int = typer.Option(10, "--limit", "-n"),
    ):
        """List items."""
        typer.echo(f"Listing items...")

    @my_plugin.command()
    def get(
        item_id: int = typer.Argument(..., help="Item ID"),
    ):
        """Get item by ID."""
        typer.echo(f"Getting item {item_id}...")
```

Usage: `ai-mini-box my-plugin list`, `ai-mini-box my-plugin get 1`

## Using the database

```python
from ai_mini_box.core.container import RepoContainer
from ai_mini_box.infrastructure.database import get_db


def register(app: typer.Typer):
    @app.command(name="my-plugin-list-contacts")
    def list_contacts():
        """List contacts from the database."""
        with get_db() as session:
            repos = RepoContainer(session)
            for c in repos.contacts.list():
                typer.echo(f"{c.id}: {c.name}")
```

## Using config

```python
from ai_mini_box.infrastructure.config import JsonConfigManager


def register(app: typer.Typer):
    @app.command(name="my-plugin-echo-config")
    def echo_config():
        config = JsonConfigManager().load()
        typer.echo(f"Poll interval: {config.poll_interval}")
```

## Logging

```python
from loguru import logger

logger.add("logs/plugin_my_plugin.log", rotation="1 MB", retention=3)
```

## Best practices

- Prefix command names to avoid conflicts (e.g., `my-plugin-*`)
- Use Typer's argument/option types for validation
- Return non-zero exit codes on errors: `raise typer.Exit(1)`
- Log errors instead of printing to stderr
- Keep `register()` clean — import actual logic from other modules
