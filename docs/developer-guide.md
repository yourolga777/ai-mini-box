# Developer Guide — Создание сервиса

## Структура пакета

Каждый сервис — отдельный Python-пакет со своей `pyproject.toml` и точкой входа.

```
packages/my-service/
├── pyproject.toml
├── src/
│   └── my_service/
│       ├── __init__.py
│       └── commands.py       # CLI-команды
└── tests/
    ├── __init__.py
    ├── conftest.py           # фикстуры (БД, конфиг)
    └── test_commands.py
```

## pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ai-mini-box-my-service"
version = "0.1.0"
description = "My service for ai-mini-box"
requires-python = ">=3.12"
dependencies = ["ai-mini-box-core>=5.0.0"]

[project.entry-points."ai_mini_box.tools"]
my-service = "my_service.commands:register"

[tool.hatch.build]
include = ["my_service/**"]
```

Ключевой элемент — `[project.entry-points."ai_mini_box.tools"]`. Функция `register` автоматически загружается ядром и получает Typer-приложение для добавления своих команд.

## Регистрация команд (commands.py)

```python
import typer
from ai_mini_box.infrastructure.database import get_db
from ai_mini_box.infrastructure.config import JsonConfigManager
from ai_mini_box.infrastructure.repositories import SqliteContactRepo

def register(app: typer.Typer):
    """Регистрирует команды сервиса в CLI."""

    @app.command()
    def my-list(
        limit: int = typer.Option(10, help="Max records"),
        config_path: str = typer.Option("data/config.json", "--config"),
    ):
        """List my entities."""
        manager = JsonConfigManager(config_path)
        config = manager.load()

        with get_db() as session:
            repo = SqliteContactRepo(session)
            items = repo.list(limit=limit)
            for item in items:
                typer.echo(f"{item.id}: {item.name}")

    @app.command()
    def my-get(
        id: int = typer.Argument(..., help="Entity ID"),
    ):
        """Get entity by ID."""
        with get_db() as session:
            repo = SqliteContactRepo(session)
            item = repo.get_by_id(id)
            if item is None:
                typer.echo("Not found")
                raise typer.Exit(code=1)
            typer.echo(f"ID: {item.id}, Name: {item.name}")
```

## RepoContainer

Для нескольких репозиториев удобнее использовать `RepoContainer`:

```python
from ai_mini_box.core.container import RepoContainer
from ai_mini_box.infrastructure.database import get_db

with get_db() as session:
    repos = RepoContainer(session)
    contacts = repos.contacts.list(limit=10)
    products = repos.products.list(limit=5)
```

Контейнер даёт доступ ко всем репозиториям:

| Атрибут | Тип | Методы |
|---|---|---|
| `repos.contacts` | `ContactRepo` | `list`, `get_by_id`, `add`, `update`, `delete`, `search` |
| `repos.products` | `ProductRepo` | `list`, `get_by_id`, `add`, `update`, `delete`, `search` |
| `repos.messages` | `MessageRepo` | `list`, `get_by_id`, `add`, `search` |
| `repos.orders` | `OrderRepo` | `list`, `get_by_id`, `add`, `update` |

## get_db() — контекстный менеджер сессии

`get_db()` открывает сессию SQLAlchemy, коммитит при успехе и откатывает при ошибке:

```python
from ai_mini_box.infrastructure.database import get_db

with get_db() as session:
    repo = SqliteContactRepo(session)
    new_contact = repo.add(Contact(name="Alice"))
    # session.commit() вызывается автоматически
    # при исключении — session.rollback()
```

Для прямого доступа к сессии (без авто-коммита):

```python
from ai_mini_box.infrastructure.database import get_session

session = get_session()
try:
    # работа с session ...
    session.commit()
except Exception:
    session.rollback()
    raise
finally:
    session.close()
```

## Конфигурация

```python
from ai_mini_box.infrastructure.config import JsonConfigManager, AppConfig

manager = JsonConfigManager("data/config.json")
config = manager.load()

# Чтение
print(config.telegram_bot_token)  # чувствительные поля расшифрованы

# Установка (сохраняет в JSON)
manager.set("poll_interval", "30")

# Сброс на дефолт
manager.unset("poll_interval")
```

Чувствительные поля (`telegram_bot_token`, `email_password`, и т.д.) автоматически шифруются при сохранении и расшифровываются при загрузке.

## Логгер

```python
from ai_mini_box.infrastructure.logger import setup_logging

logger = setup_logging(verbose=True)
logger.info("Service started")
logger.debug("Detail: {}", some_var)
```

## Тестирование

### conftest.py

```python
import pytest
from typer.testing import CliRunner
from ai_mini_box.infrastructure.database import init_db, dispose_engine

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def db():
    init_db(":memory:")
    yield
    dispose_engine()
```

### test_commands.py

```python
from your_package.commands import app  # или register()

def test_list(runner, db):
    result = runner.invoke(app, ["my-list"])
    assert result.exit_code == 0
```

Для интеграционных тестов используйте `CliRunner` + временный config.

## Обработка ошибок

```python
from ai_mini_box.core.exceptions import NotFoundError

try:
    item = repo.get_by_id(id)
except NotFoundError:
    typer.echo("Not found", err=True)
    raise typer.Exit(code=1)
```

## Публикация

```bash
pip install hatchling twine
cd packages/my-service
hatchling build
twine upload dist/*
```

Или через CI — создайте тег `v*` и publish.yml опубликует автоматически.

## Пример: демо-сервис

Готовый пример — `packages/demo/`. Скопируйте его как стартовый шаблон:

- `pyproject.toml` — entry point `demo = "ai_mini_box_demo.commands:register"`
- `commands.py` — 3 команды: `demo-list`, `demo-get`, `demo-add`
- `tests/` — 5 unit + 4 E2E теста
