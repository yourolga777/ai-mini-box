# Developer Guide — Создание сервиса для ai-mini-box-core

Это руководство описывает процесс разработки нового сервиса (плагина) для экосистемы ai-mini-box. Плагин — это отдельный Python-пакет, который подключается к ядру через entry point и добавляет свои CLI-команды, а при необходимости — фоновые процессы (демоны) и интеграцию с PWA‑интерфейсом.

## Структура пакета

Рекомендуемая структура для нового сервиса (замените `my_service` на имя вашего сервиса):
packages/my-service/
├── pyproject.toml
├── README.md
├── src/
│ └── my_service/
│ ├── init.py
│ ├── commands.py # регистрация команд
│ ├── core.py # основная логика (опционально)
│ └── exceptions.py (опционально)
└── tests/
├── init.py
├── conftest.py # фикстуры (БД, конфиг, CliRunner)
├── unit/
│ ├── init.py
│ └── test_commands.py
└── integration/
├── init.py
└── test_cli.py

text

Вместо `src/` можно использовать плоскую структуру (как в демо-сервисе), но `src/`‑layout считается хорошей практикой для избежания конфликтов импорта.

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
dependencies = [
    "ai-mini-box-core>=5.0.0",
    # другие зависимости, например, requests, python-telegram-bot
]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-cov>=5"]

[project.entry-points."ai_mini_box.tools"]
my-service = "my_service.commands:register"

[tool.hatch.build]
include = ["my_service/**"]
Ключевой элемент — [project.entry-points."ai_mini_box.tools"]. Функция register автоматически загружается ядром и получает Typer-приложение для добавления своих команд.

Регистрация команд (commands.py)
python
import typer
from ai_mini_box.core.container import RepoContainer
from ai_mini_box.infrastructure.database import get_db
from ai_mini_box.infrastructure.config import JsonConfigManager
from ai_mini_box.core.exceptions import NotFoundError

# Создаём подгруппу команд (опционально)
service_app = typer.Typer(help="Commands for my service")

@service_app.command()
def list(
    limit: int = typer.Option(10, help="Max records"),
    offset: int = typer.Option(0, help="Offset"),
):
    """List contacts."""
    with get_db() as session:
        repos = RepoContainer(session)
        contacts = repos.contacts.list(limit=limit, offset=offset)
        for c in contacts:
            typer.echo(f"{c.id}: {c.name} ({c.phone or '—'})")

@service_app.command()
def get(
    id: int = typer.Argument(..., help="Contact ID"),
):
    """Get contact by ID."""
    with get_db() as session:
        repos = RepoContainer(session)
        try:
            contact = repos.contacts.get_by_id(id)
            if contact is None:
                raise NotFoundError("Contact", id)
            typer.echo(f"ID: {contact.id}")
            typer.echo(f"Name: {contact.name}")
            typer.echo(f"Phone: {contact.phone or '—'}")
        except NotFoundError as e:
            typer.echo(f"Error: {e.message}", err=True)
            raise typer.Exit(code=e.exit_code)

@service_app.command()
def add(
    name: str = typer.Argument(..., help="Contact name"),
    phone: str = typer.Option("", help="Phone number"),
    email: str = typer.Option("", help="Email address"),
):
    """Add a new contact."""
    from ai_mini_box.core.models import Contact
    with get_db() as session:
        repos = RepoContainer(session)
        contact = Contact(name=name, phone=phone, email=email)
        added = repos.contacts.add(contact)
        typer.echo(f"Added contact with ID: {added.id}")

# Основная функция регистрации
def register(app: typer.Typer):
    """Регистрирует команды сервиса в CLI."""
    app.add_typer(service_app, name="my-service")
Использование репозиториев через RepoContainer
RepoContainer предоставляет доступ ко всем репозиториям через свойства:

Атрибут	Тип	Методы
repos.contacts	ContactRepo	list, get_by_id, add, update, delete, search
repos.products	ProductRepo	list, get_by_id, add, update, delete, search
repos.messages	MessageRepo	list, get_by_id, add, search
repos.orders	OrderRepo	list, get_by_id, add, update
Все методы репозиториев работают с Pydantic-моделями (Contact, Product, Message, Order), определёнными в core.models.

get_db() — контекстный менеджер сессии
get_db() открывает сессию SQLAlchemy, автоматически выполняет commit при успехе и rollback при исключении:

python
from ai_mini_box.infrastructure.database import get_db

with get_db() as session:
    repos = RepoContainer(session)
    new_contact = repos.contacts.add(Contact(name="Alice"))
    # session.commit() вызывается автоматически
    # при исключении — session.rollback()
Если вам нужен прямой доступ к сессии без авто-коммита (например, для сложных транзакций), используйте get_session() (низкоуровневая функция, но лучше использовать get_db для простоты).

Конфигурация
python
from ai_mini_box.infrastructure.config import JsonConfigManager, AppConfig

manager = JsonConfigManager("data/config.json")
config = manager.load()

# Чтение
print(config.telegram_token)  # чувствительные поля расшифрованы

# Установка значения (сохраняет в JSON)
manager.set("poll_interval", 60)

# Сброс на значение по умолчанию
manager.unset("poll_interval")
Чувствительные поля (перечислены в SENSITIVE_FIELDS в config.py) автоматически шифруются при сохранении и расшифровываются при загрузке.

Логирование
python
from loguru import logger

logger.info("Service started")
logger.debug("Detail: {}", some_var)
Логи пишутся в консоль и в файл logs/ai-mini-box.log с ротацией (1 МБ × 3 файла). Для отдельного файла логов вашего плагина рекомендуется добавить:

python
logger.add("logs/plugin_my_service.log", rotation="1 MB", retention=3)
Это позволит веб-интерфейсу показывать логи плагина отдельно.

Фоновые процессы (демоны)
Если ваш сервис должен работать в фоне (например, опрос API), добавьте команду daemon. Эта команда будет отображаться в PWA‑интерфейсе и может быть запущена/остановлена через веб‑интерфейс.

python
import time
from ai_mini_box.infrastructure.config import JsonConfigManager
from loguru import logger

@service_app.command()
def daemon():
    """Запускает фоновый процесс."""
    config = JsonConfigManager().load()
    # Проверяем необходимые настройки
    if not config.telegram_token:
        typer.echo("Error: telegram_token not set", err=True)
        raise typer.Exit(1)

    logger.info("Daemon started")
    while True:
        try:
            # Ваша логика опроса
            logger.debug("Polling...")
            time.sleep(config.poll_interval)
        except KeyboardInterrupt:
            logger.info("Daemon stopped by user")
            break
        except Exception as e:
            logger.error(f"Daemon error: {e}")
            time.sleep(5)
Важно: демон должен корректно обрабатывать сигналы SIGTERM (можно через signal.signal), чтобы завершаться при остановке из PWA.

Интеграция с PWA
PWA автоматически обнаруживает установленные плагины через entry points. Для каждого плагина в интерфейсе отображается карточка с названием, статусом (запущен/остановлен) и кнопками управления (если у плагина есть команда daemon).

Чтобы ваш плагин правильно отображался в PWA:

Убедитесь, что entry point зарегистрирован.

Если есть команда daemon, она будет автоматически распознана по имени.

Логи, записываемые в стандартный логгер, будут доступны в интерфейсе (если вы используете отдельный файл, укажите его в настройках PWA – пока логгер core пишет в общий файл, но мы рекомендуем добавлять отдельный файл для чёткого разделения).

Обработка ошибок
python
from ai_mini_box.core.exceptions import NotFoundError, AppError

try:
    item = repo.get_by_id(id)
except NotFoundError as e:
    typer.echo(f"Error: {e.message}", err=True)
    raise typer.Exit(code=e.exit_code)
except AppError as e:
    typer.echo(f"Application error: {e.message}", err=True)
    raise typer.Exit(code=e.exit_code)
Тестирование
conftest.py
python
import pytest
from typer.testing import CliRunner
from ai_mini_box.infrastructure.database import init_db, dispose_engine

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def db_session():
    # Используем временную БД в памяти
    init_db(":memory:")
    from ai_mini_box.infrastructure.database import SessionLocal
    session = SessionLocal()
    yield session
    session.close()
    dispose_engine()
test_commands.py (unit)
python
from typer.testing import CliRunner
from my_service.commands import service_app

def test_list(runner, db_session):
    result = runner.invoke(service_app, ["list"])
    assert result.exit_code == 0
    # Проверяем вывод
Для интеграционных тестов можно использовать CliRunner с основным приложением ai_mini_box.cli:app и проверять, что команда зарегистрирована.

Smoke-тест регистрации
python
def test_cli_help(runner):
    from ai_mini_box.cli import app
    result = runner.invoke(app, ["--help"])
    assert "my-service" in result.output
Публикация
bash
pip install hatchling twine
cd packages/my-service
hatch build
twine upload dist/*
Или используйте GitHub Actions: при создании тега v* автоматически запускается publish.yml, который публикует пакет на PyPI (если настроен).

Пример: демо-сервис
Готовый пример — packages/demo/ в репозитории core. Скопируйте его как стартовый шаблон:

pyproject.toml — entry point demo = "ai_mini_box_demo.commands:register"

commands.py — 3 команды: demo-list, demo-get, demo-add

tests/ — 5 unit + 4 E2E теста

Заключение
Следуя этому руководству, вы сможете быстро создавать новые сервисы для экосистемы ai-mini-box. Если возникнут вопросы, изучите исходный код ядра и демо-сервиса, или обратитесь к документации проекта.

text

---
