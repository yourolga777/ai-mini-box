# Full Plugin Example

This example shows a complete plugin that monitors product stock levels and sends notifications.

## Directory structure

```
ai-mini-box-stockwatch/
├── ai_mini_box_stockwatch/
│   ├── __init__.py
│   ├── commands.py
│   ├── watcher.py
│   └── help/
│       00-installation.md
│       01-commands.md
├── tests/
│   ├── __init__.py
│   ├── test_commands.py
│   └── test_watcher.py
├── pyproject.toml
├── README.md
└── LICENSE
```

## pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ai-mini-box-stockwatch"
version = "0.1.0"
description = "Stock level monitoring plugin for ai-mini-box"
requires-python = ">=3.12"
readme = "README.md"
license = { file = "LICENSE" }
dependencies = [
    "ai-mini-box-core>=5.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-mock>=3"]

[project.entry-points."ai_mini_box.tools"]
stockwatch = "ai_mini_box_stockwatch.commands:register"

[project.entry-points."ai_mini_box.help"]
stockwatch = "ai_mini_box_stockwatch"

[tool.hatch.build]
include = ["ai_mini_box_stockwatch/**"]
```

## commands.py

```python
import typer
from loguru import logger
from ai_mini_box.core.container import RepoContainer
from ai_mini_box.infrastructure.database import get_db
from ai_mini_box.infrastructure.config import JsonConfigManager

logger.add("logs/plugin_stockwatch.log", rotation="1 MB", retention=3)


def register(app: typer.Typer):
    sw = typer.Typer(help="Stock monitoring commands")
    app.add_typer(sw, name="stockwatch")

    @sw.command()
    def check(threshold: int = typer.Option(5, help="Min stock threshold")):
        """List products with stock below threshold."""
        with get_db() as session:
            repos = RepoContainer(session)
            low_stock = [
                p for p in repos.products.list()
                if p.stock < threshold
            ]
            if not low_stock:
                typer.echo("All products above threshold.")
                return
            for p in low_stock:
                typer.echo(f"{p.name}: stock={p.stock} (below {threshold})")
            logger.warning(f"Found {len(low_stock)} products below threshold")

    @sw.command()
    def daemon():
        """Run continuous stock monitoring."""
        config = JsonConfigManager().load()
        logger.info(f"StockWatch daemon started (interval={config.poll_interval}s)")
        while True:
            try:
                with get_db() as session:
                    repos = RepoContainer(session)
                    low_stock = [p for p in repos.products.list() if p.stock < 5]
                    if low_stock:
                        names = ", ".join(p.name for p in low_stock)
                        logger.warning(f"Low stock: {names}")
            except Exception as e:
                logger.error(f"Check error: {e}")
            import time
            time.sleep(config.poll_interval)
```

## watcher.py

```python
from ai_mini_box.core.models import Product


def find_low_stock(products: list[Product], threshold: int = 5) -> list[Product]:
    """Filter products whose stock is below threshold."""
    return [p for p in products if p.stock < threshold]
```

## help/00-installation.md

```markdown
# Stock Watch Plugin

Monitors product stock levels and alerts when inventory runs low.

## Install

```bash
pip install ai-mini-box-stockwatch
```

## Commands

- `ai-mini-box stockwatch check --threshold 5` — one-time check
- `ai-mini-box stockwatch daemon` — continuous monitoring
```
```

## tests/test_watcher.py

```python
from ai_mini_box_stockwatch.watcher import find_low_stock
from ai_mini_box.core.models import Product


def test_find_low_stock_returns_low_items():
    products = [
        Product(name="A", stock=2),
        Product(name="B", stock=10),
        Product(name="C", stock=0),
    ]
    result = find_low_stock(products, threshold=5)
    assert [p.name for p in result] == ["A", "C"]


def test_find_low_stock_empty_when_all_ok():
    products = [Product(name="A", stock=10), Product(name="B", stock=20)]
    assert find_low_stock(products, threshold=5) == []
```

## tests/test_commands.py (integration)

```python
from typer.testing import CliRunner
from ai_mini_box.cli import app


def test_check_command_registered():
    runner = CliRunner()
    result = runner.invoke(app, ["stockwatch", "--help"])
    assert result.exit_code == 0
    assert "check" in result.output
```

## After publishing

Users install and use:

```bash
pip install ai-mini-box-stockwatch
ai-mini-box stockwatch check --threshold 3
```
