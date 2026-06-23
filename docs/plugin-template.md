Шаблон разработки нового плагина для ai-mini-box-core
Это пошаговая инструкция, которую следует применять при создании каждого нового сервиса (плагина). Она включает минимальный набор действий, структуру, код и тесты.

Шаг 0. Подготовка
Создайте новую директорию для плагина (например, packages/<plugin-name>).

Инициализируйте Git-репозиторий (если ещё нет).

Убедитесь, что ядро (ai-mini-box-core) установлено в режиме разработки:

bash
pip install -e packages/core/
Шаг 1. Структура пакета
Создайте следующую структуру:

text
packages/<plugin-name>/
├── pyproject.toml
├── README.md
├── ai_mini_box_<plugin>/
│   ├── __init__.py
│   ├── commands.py          # регистрация команд
│   ├── core.py              # основная логика (опционально)
│   └── exceptions.py        (опционально)
└── tests/
    ├── __init__.py
    ├── unit/
    │   ├── __init__.py
    │   └── test_commands.py
    └── integration/
        ├── __init__.py
        └── test_cli.py
Шаг 2. pyproject.toml
Заполните файл:

toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ai-mini-box-<plugin>"
version = "0.1.0"
description = "Описание вашего плагина"
requires-python = ">=3.12"
dependencies = [
    "ai-mini-box-core>=5.0.0",
    # другие зависимости, например, requests, python-telegram-bot и т.д.
]
[project.optional-dependencies]
dev = ["pytest>=8"]

[project.entry-points."ai_mini_box.tools"]
<plugin> = "ai_mini_box_<plugin>.commands:register"

[tool.hatch.build]
include = ["ai_mini_box_<plugin>/**"]
Замените <plugin> на имя вашего сервиса (например, telegram, email, whatsapp).

Шаг 3. Команды CLI
В файле commands.py:

python
import typer
from ai_mini_box.core.container import RepoContainer
from ai_mini_box.infrastructure.database import get_db
from ai_mini_box.infrastructure.config import JsonConfigManager
from loguru import logger

# Создаём подгруппу команд
plugin_app = typer.Typer(help="Commands for <plugin>")

@plugin_app.command()
def hello():
    """Пример команды."""
    typer.echo("Hello from <plugin>!")

# Основная функция регистрации
def register(app: typer.Typer):
    app.add_typer(plugin_app, name="<plugin>")
Шаг 4. Фоновый процесс (если нужен)
Если ваш плагин должен работать в фоне (демон), добавьте команду daemon:

python
import time
from ai_mini_box.infrastructure.logger import logger

@plugin_app.command()
def daemon():
    """Запускает фоновый процесс опроса."""
    config = JsonConfigManager().load()
    # Проверка необходимых настроек
    if not config.telegram_token:
        typer.echo("Error: telegram_token not set")
        raise typer.Exit(1)

    logger.info("Daemon started")
    while True:
        try:
            # Ваша логика
            logger.debug("Polling...")
            time.sleep(config.poll_interval)
        except KeyboardInterrupt:
            logger.info("Daemon stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in daemon: {e}")
            time.sleep(5)
Эта команда будет автоматически отображаться в веб-интерфейсе для управления (запуск/остановка). Убедитесь, что она пишет логи в стандартный логгер или в отдельный файл.

Шаг 5. Использование репозиториев
Пример команды, сохраняющей данные:

python
@plugin_app.command()
def process():
    with get_db() as session:
        container = RepoContainer(session)
        messages = container.messages.list()
        for msg in messages:
            # обработка
            pass
        session.commit()
Шаг 6. Тестирование
Создайте тесты, используя фикстуры из core (если они экспортируются) или собственные.

Пример unit-теста:

python
import pytest
from typer.testing import CliRunner
from ai_mini_box.cli import app
from ai_mini_box.tests.mocks import MockContactRepo

def test_hello_command():
    runner = CliRunner()
    result = runner.invoke(app, ["<plugin>", "hello"])
    assert result.exit_code == 0
    assert "Hello from <plugin>" in result.output
Интеграционные тесты могут использовать временную БД:

python
def test_integration(cli_runner, db_session):
    # ... используйте db_session для проверки сохранения данных
Шаг 7. Документация
Обновите README плагина, указав:

Установку: pip install ai-mini-box-<plugin>

Настройку (какие поля конфига нужны)

Примеры команд

Шаг 8. Публикация
Убедитесь, что все тесты проходят: pytest tests/

Соберите пакет: hatch build

Опубликуйте на PyPI: twine upload dist/*

После публикации ваш плагин станет доступен для установки пользователями.

Чек-лист перед релизом
Имя пакета соответствует ai-mini-box-<plugin>

Entry point зарегистрирован

Все команды имеют docstrings

Есть хотя бы один тест

README содержит инструкцию по установке и использованию

Версия в pyproject.toml соответствует семантическому версионированию

Зависимости указаны корректно

Плагин не импортирует другие плагины (только core)

Заключение
Следуя этому шаблону, вы сможете быстро создавать новые сервисы для экосистемы ai-mini-box. Если у вас возникнут вопросы, обращайтесь к руководству разработчика (developer-guide.md) или к исходному коду ядра и демо-плагина.
