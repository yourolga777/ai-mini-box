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
import signal
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
        stop = False

        def _signal_handler(signum, frame):
            nonlocal stop
            stop = True
            logger.info("Shutdown requested...")

        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

        while not stop:
            try:
                # Ваша логика
                logger.debug("Polling...")
            except Exception as e:
                logger.error(f"Error in daemon: {e}")

            if stop:
                break
            time.sleep(config.poll_interval)

        logger.info("Daemon stopped")
Эта команда будет автоматически отображаться в веб-интерфейсе для управления (запуск/остановка). Убедитесь, что она пишет логи в стандартный логгер или в отдельный файл.

Шаг 5. Использование репозиториев
Пример команды, сохраняющей данные (auto-commit через `get_db()`):

python
@plugin_app.command()
def process():
    with get_db() as session:
        container = RepoContainer(session)
        messages = container.messages.list()
        for msg in messages:
            # обработка
            pass
        # session.commit() вызывается автоматически

Шаг 6. Регистрация сервиса (опционально)
Если ваш плагин предоставляет API для других плагинов (LLM, нотификации и т.п.), зарегистрируйте его в реестре сервисов:

python
from ai_mini_box.core.services.registry import register_service
from ai_mini_box.core.services.llm import LlmService

def register(app: typer.Typer):
    register_service("my_service", MyServiceImpl())
    app.add_typer(plugin_app, name="<plugin>")

Шаг 7. Тестирование
Используйте моки из `ai_mini_box.testing` — они не требуют БД:

python
from ai_mini_box.testing import MockContactRepo, MockMessageRepo
from ai_mini_box.core.models import Contact, Message

def test_my_logic():
    repo = MockContactRepo()
    c = repo.add(Contact(name="Test"))
    assert repo.get_by_id(1).name == "Test"

Интеграционные тесты с in-memory SQLite:

python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ai_mini_box.infrastructure.database import Base
from ai_mini_box.infrastructure import orm_models  # noqa: F401

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()

**Не используйте `init_db()` в тестах** — он не создаёт таблицы.

Шаг 8. Документация
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

Плагин использует `ai_mini_box.testing` для моков (не `ai_mini_box.tests.mocks`)

Заключение
Следуя этому шаблону, вы сможете быстро создавать новые сервисы для экосистемы ai-mini-box. Если у вас возникнут вопросы, обращайтесь к руководству разработчика (developer-guide.md) или к исходному коду ядра и демо-плагина.
