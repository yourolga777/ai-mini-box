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

## Daemon (background process)

If your plugin needs to run continuously (e.g., polling), add a `daemon` command. The web UI manages daemon lifecycle via start/stop buttons.

```python
import signal
import time
from loguru import logger
from ai_mini_box.infrastructure.config import JsonConfigManager

logger.add("logs/plugin_my_plugin.log", rotation="1 MB", retention=3)


def register(app: typer.Typer):
    my_plugin = typer.Typer(help="My plugin")
    app.add_typer(my_plugin, name="my-plugin")

    @my_plugin.command()
    def daemon():
        """Run continuous polling loop until interrupted."""
        # Load config fresh each cycle — see "Read config every cycle" below
        config = JsonConfigManager().load()
        # Validate required config
        if not config.telegram_token:
            typer.echo("Error: token not set")
            raise typer.Exit(1)

        logger.info("Daemon started")

        stop = False

        def _signal_handler(signum, frame):
            nonlocal stop
            stop = True
            logger.info("Shutdown requested, finishing current cycle...")

        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

        while not stop:
            try:
                # Your polling logic here
                logger.debug("Polling...")
            except Exception as e:
                logger.error(f"Polling error: {e}")

            if stop:
                break
            time.sleep(config.poll_interval)

        logger.info("Daemon stopped")
```

### How the web UI manages daemons

When the user clicks **Start daemon** in the web interface, the server spawns the daemon as a subprocess:

```
ai-mini-box my-plugin daemon
```

- stdout/stderr are redirected to `logs/plugin_<name>.log`
- The PID is saved to `data/daemon_pids.json`
- On **Stop daemon**, the process is killed (SIGTERM on Unix, `taskkill` on Windows)
- If the server restarts, it checks which PIDs are still alive and updates their status

Write logs with `logger.info/error` — they appear in the web UI under the plugin's log viewer.

### Read config every cycle

Do NOT load config once at daemon startup — it will miss changes made via the web UI. Call `JsonConfigManager().load()` **inside the loop** (or at least check a reload signal):

```python
while not stop:
    config = JsonConfigManager().load()  # fresh each cycle
    # ... your polling logic ...
    time.sleep(config.poll_interval)
```

This ensures config changes (token, allowed IDs, interval) take effect without a restart.

## Best practices

- Prefix command names to avoid conflicts (e.g., `my-plugin-*`)
- Use Typer's argument/option types for validation
- Return non-zero exit codes on errors: `raise typer.Exit(1)`
- Log errors instead of printing to stderr
- Keep `register()` clean — import actual logic from other modules
