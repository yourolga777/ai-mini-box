# Промпт: Реализация ai-mini-box-core

## Описание

Реализовать базовый пакет `ai-mini-box-core` — каркас для системы CLI-инструментов автоматизации малого бизнеса. Core — единственный обязательный пакет, все остальные сервисы подключаются как отдельные pip-пакеты и автоматически регистрируются в CLI.

## Технологии

- Python 3.12+
- Typer — CLI-фреймворк
- SQLAlchemy 2.0 (синхронный) — ORM
- loguru — логирование
- pytest — тестирование

## Структура пакета

```
ai-mini-box-core/
├── pyproject.toml
└── ai_mini_box/
    ├── __init__.py
    ├── __main__.py                   # python -m ai_mini_box → cli.app()
    ├── cli.py                        # главная Typer-группа + авто-поиск tools/
    │
    ├── core/                         # ★ Абстракции (не зависят от БД)
    │   ├── __init__.py
    │   ├── models.py                 # dataclass'ы всех сущностей
    │   ├── repositories.py           # ABC репозиториев
    │   └── exceptions.py             # кастомные исключения
    │
    ├── infrastructure/               # ★ Реализации (SQLAlchemy, JSON, etc.)
    │   ├── __init__.py
    │   ├── database.py               # engine, sessionmaker, init_db(), get_db()
    │   ├── config.py                 # JsonConfigManager (чтение/запись/шифрование)
    │   ├── logger.py                 # настройка loguru
    │   └── repositories/             # SQLAlchemy реализации
    │       ├── __init__.py
    │       ├── contact_repo.py
    │       ├── product_repo.py
    │       ├── message_repo.py
    │       ├── order_repo.py
    │       └── task_repo.py
    │
    ├── tools/                        # ★ Точка подключения сервисов
    │   └── __init__.py               # пустой, для namespace packages
    │
    └── tests/
        ├── __init__.py
        ├── conftest.py               # общие фикстуры для всех сервисов
        ├── mocks.py                  # MockContactRepo, MockProductRepo, ...
        ├── test_registry.py          # smoke-тест: все ли команды зарегистрированы
        └── integration/
            ├── __init__.py
            ├── conftest.py           # фикстуры для интеграционных тестов
            └── README.md             # правила написания тестов
```

## Детальная реализация

### 1. pyproject.toml

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "ai-mini-box-core"
version = "4.0.0"
description = "AI mini box — ядро системы автоматизации малого бизнеса"
requires-python = ">=3.12"
dependencies = [
    "typer>=0.12",
    "SQLAlchemy>=2.0",
    "loguru>=0.7",
    "pydantic>=2.0",
]
optional-dependencies = {
    dev = ["pytest>=8", "pytest-cov>=5"],
}
[project.scripts]
ai-mini-box = "ai_mini_box.cli:app"
```

### 2. cli.py — главная точка входа

```python
import importlib
import pkgutil
import typer
import ai_mini_box.tools

app = typer.Typer(
    name="ai-mini-box",
    help="AI mini box — автоматизация малого бизнеса",
    no_args_is_help=True,
)

# Автоматическая регистрация всех установленных инструментов
for module_info in pkgutil.iter_modules(ai_mini_box.tools.__path__):
    if module_info.name.startswith("_"):
        continue
    module = importlib.import_module(f"ai_mini_box.tools.{module_info.name}")
    if hasattr(module, "register"):
        module.register(app)
```

**Важно:** каждый сервис экспортирует функцию `register(app: typer.Typer)`, которая добавляет свою подгруппу команд. Никакой ручной регистрации в cli.py не требуется.

### 3. core/models.py — модели данных

```python
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional

class Topic(str, Enum):
    PRICES = "Цены"
    ORDER = "Заказ"
    COMPLAINT = "Жалоба"
    SCHEDULE = "График"
    OTHER = "Другое"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class MessageSource(str, Enum):
    TELEGRAM = "telegram"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    MANUAL = "manual"

class OrderStatus(str, Enum):
    NEW = "new"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

@dataclass
class Contact:
    id: Optional[int] = None
    name: str = ""
    phone: Optional[str] = None
    email: Optional[str] = None
    telegram: Optional[str] = None
    whatsapp: Optional[str] = None
    source: MessageSource = MessageSource.MANUAL
    notes: Optional[str] = None
    total_spent: int = 0  # в копейках
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class Product:
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    price_kopecks: int = 0
    stock: int = 0
    unit: str = "шт"
    category: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Message:
    id: Optional[int] = None
    source: MessageSource = MessageSource.MANUAL
    external_id: Optional[str] = None
    chat_id: Optional[str] = None
    contact_id: Optional[int] = None
    text: str = ""
    topic: Optional[Topic] = None
    draft_response: Optional[str] = None
    sent_response: bool = False
    received_at: datetime = field(default_factory=datetime.now)

@dataclass
class Order:
    id: Optional[int] = None
    contact_id: Optional[int] = None
    status: OrderStatus = OrderStatus.NEW
    total_kopecks: int = 0
    notes: Optional[str] = None
    source_message_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class Task:
    id: Optional[int] = None
    title: str = ""
    description: Optional[str] = None
    due_date: date = field(default_factory=date.today)
    due_time: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: str = "pending"
    contact_id: Optional[int] = None
    assignee: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
```

### 4. core/repositories.py — абстрактные репозитории

```python
from abc import ABC, abstractmethod
from typing import Optional, List
from .models import Contact, Product, Message, Order, Task

class ContactRepo(ABC):
    @abstractmethod
    def list(self, limit: int = 20, offset: int = 0, sort: str = "name") -> list[Contact]: ...
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Contact]: ...
    @abstractmethod
    def add(self, contact: Contact) -> Contact: ...
    @abstractmethod
    def update(self, contact: Contact) -> Contact: ...
    @abstractmethod
    def delete(self, id: int) -> bool: ...
    @abstractmethod
    def search(self, query: str) -> list[Contact]: ...

class ProductRepo(ABC):
    @abstractmethod
    def list(self, limit: int = 20, offset: int = 0, sort: str = "name") -> list[Product]: ...
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Product]: ...
    @abstractmethod
    def add(self, product: Product) -> Product: ...
    @abstractmethod
    def update(self, product: Product) -> Product: ...
    @abstractmethod
    def delete(self, id: int) -> bool: ...
    @abstractmethod
    def search(self, query: str) -> list[Product]: ...

class MessageRepo(ABC):
    @abstractmethod
    def list(self, limit: int = 20, offset: int = 0) -> list[Message]: ...
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Message]: ...
    @abstractmethod
    def add(self, message: Message) -> Message: ...
    @abstractmethod
    def search(self, query: str, topic: Optional[str] = None) -> list[Message]: ...

class OrderRepo(ABC):
    @abstractmethod
    def list(self, limit: int = 20, offset: int = 0) -> list[Order]: ...
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Order]: ...
    @abstractmethod
    def add(self, order: Order) -> Order: ...
    @abstractmethod
    def update(self, order: Order) -> Order: ...

class TaskRepo(ABC):
    @abstractmethod
    def query(self) -> QueryBuilder: ...
    @abstractmethod
    def list(self, limit: int = 50, offset: int = 0, **filters) -> list[Task]: ...
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Task]: ...
    @abstractmethod
    def add(self, task: Task) -> Task: ...
    @abstractmethod
    def update(self, task: Task) -> Task: ...
    @abstractmethod
    def delete(self, id: int) -> bool: ...
```

### 5. core/exceptions.py

```python
class AppError(Exception):
    """Базовая ошибка приложения."""
    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)

class NotFoundError(AppError):
    """Сущность не найдена."""
    def __init__(self, entity: str, id: int):
        super().__init__(f"{entity} with id {id} not found", exit_code=2)

class ConfigError(AppError):
    """Ошибка конфигурации."""
    def __init__(self, message: str):
        super().__init__(message, exit_code=3)
```

### 6. infrastructure/database.py

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pathlib import Path

class Base(DeclarativeBase):
    pass

_engine = None
_SessionLocal = None

def get_db_path() -> Path:
    return Path("data/app.db")

def init_db(db_path: str | Path | None = None):
    global _engine, _SessionLocal
    db_path = Path(db_path) if db_path else get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    _engine = create_engine(f"sqlite:///{db_path}", echo=False)
    _SessionLocal = sessionmaker(bind=_engine)
    Base.metadata.create_all(_engine)

def get_db():
    global _SessionLocal
    if _SessionLocal is None:
        init_db()
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 7. infrastructure/config.py

```python
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class AppConfig:
    telegram_token: str = ""
    telegram_allowed_chat_ids: list[int] = None
    email_imap_server: str = "imap.yandex.ru"
    email_imap_port: int = 993
    email_login: str = ""
    email_password: str = ""
    llm_model_path: str = "models/Phi-3-mini-q4.gguf"
    llm_n_ctx: int = 4096
    llm_n_threads: int = 4
    poll_interval: int = 30
    auto_backup_interval: int = 0
    work_schedule_start: str = "09:00"
    work_schedule_end: str = "18:00"

class JsonConfigManager:
    def __init__(self, path: str | Path = "data/config.json"):
        self.path = Path(path)

    def load(self) -> AppConfig:
        if not self.path.exists():
            return AppConfig()
        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        return AppConfig(**data)

    def save(self, config: AppConfig):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(asdict(config), f, ensure_ascii=False, indent=2)
```

### 8. infrastructure/logger.py

```python
import sys
from loguru import logger

def setup_logging(verbose: bool = False):
    logger.remove()
    level = "DEBUG" if verbose else "INFO"
    logger.add(sys.stdout, format="{time:HH:mm:ss} | {level:<7} | {message}", level=level)
    return logger
```

### 9. tests/conftest.py — фикстуры для всех сервисов

```python
import pytest
from typer.testing import CliRunner
from pathlib import Path
import tempfile
import json

from ai_mini_box.core.models import Contact, Product, Message, Task
from ai_mini_box.tests.mocks import MockContactRepo, MockProductRepo, MockMessageRepo, MockTaskRepo

@pytest.fixture
def cli_runner():
    return CliRunner()

@pytest.fixture
def tmp_config(tmp_path: Path):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({
        "telegram_token": "test:token",
        "email_imap_server": "imap.test.com",
        "email_login": "test@test.com",
        "email_password": "",
        "poll_interval": 30,
    }))
    return config

@pytest.fixture
def mock_contact_repo():
    return MockContactRepo()

@pytest.fixture
def mock_product_repo():
    return MockProductRepo()

@pytest.fixture
def mock_message_repo():
    return MockMessageRepo()

@pytest.fixture
def mock_task_repo():
    return MockTaskRepo()
```

### 10. tests/mocks.py — mock-репозитории для unit-тестов

```python
from typing import Optional
from ai_mini_box.core.models import Contact, Product, Message, Task
from ai_mini_box.core.repositories import ContactRepo, ProductRepo, MessageRepo, TaskRepo

class MockContactRepo(ContactRepo):
    def __init__(self):
        self._contacts: dict[int, Contact] = {}
        self._next_id = 1

    def list(self, limit=20, offset=0, sort="name"):
        items = sorted(self._contacts.values(), key=lambda c: getattr(c, sort))
        return items[offset:offset + limit]

    def get_by_id(self, id: int) -> Optional[Contact]:
        return self._contacts.get(id)

    def add(self, contact: Contact) -> Contact:
        contact.id = self._next_id
        self._contacts[self._next_id] = contact
        self._next_id += 1
        return contact

    def update(self, contact: Contact) -> Contact:
        if contact.id in self._contacts:
            self._contacts[contact.id] = contact
        return contact

    def delete(self, id: int) -> bool:
        return self._contacts.pop(id, None) is not None

    def search(self, query: str) -> list[Contact]:
        return [c for c in self._contacts.values() if query.lower() in c.name.lower()]

class MockProductRepo(ProductRepo):
    def __init__(self):
        self._products: dict[int, Product] = {}
        self._next_id = 1

    def list(self, limit=20, offset=0, sort="name"):
        items = sorted(self._products.values(), key=lambda p: getattr(p, sort))
        return items[offset:offset + limit]

    def get_by_id(self, id: int) -> Optional[Product]:
        return self._products.get(id)

    def add(self, product: Product) -> Product:
        product.id = self._next_id
        self._products[self._next_id] = product
        self._next_id += 1
        return product

    def update(self, product: Product) -> Product:
        if product.id in self._products:
            self._products[product.id] = product
        return product

    def delete(self, id: int) -> bool:
        return self._products.pop(id, None) is not None

    def search(self, query: str) -> list[Product]:
        return [p for p in self._products.values() if query.lower() in p.name.lower()]

class MockMessageRepo(MessageRepo):
    def __init__(self):
        self._messages: dict[int, Message] = {}
        self._next_id = 1

    def list(self, limit=20, offset=0):
        items = list(self._messages.values())
        return items[offset:offset + limit]

    def get_by_id(self, id: int) -> Optional[Message]:
        return self._messages.get(id)

    def add(self, message: Message) -> Message:
        message.id = self._next_id
        self._messages[self._next_id] = message
        self._next_id += 1
        return message

    def search(self, query: str, topic: Optional[str] = None):
        results = [m for m in self._messages.values() if query.lower() in m.text.lower()]
        if topic:
            results = [m for m in results if m.topic and m.topic.value == topic]
        return results

class MockTaskRepo(TaskRepo):
    def __init__(self):
        self._tasks: dict[int, Task] = {}
        self._next_id = 1

    def query(self):
        from ai_mini_box.core.repositories import QueryBuilder
        return QueryBuilder(list(self._tasks.values()))

    def list(self, limit=50, offset=0, **filters):
        items = list(self._tasks.values())
        for key, value in filters.items():
            if value is not None:
                items = [t for t in items if getattr(t, key, None) == value]
        items.sort(key=lambda t: (t.due_date, t.due_time or ""))
        return items[offset:offset + limit]

    def get_by_id(self, id: int) -> Optional[Task]:
        return self._tasks.get(id)

    def add(self, task: Task) -> Task:
        task.id = self._next_id
        self._tasks[self._next_id] = task
        self._next_id += 1
        return task

    def update(self, task: Task) -> Task:
        if task.id in self._tasks:
            self._tasks[task.id] = task
        return task

    def delete(self, id: int) -> bool:
        return self._tasks.pop(id, None) is not None
```

### 11. tests/test_registry.py — smoke-тест

```python
from typer.testing import CliRunner
from ai_mini_box.cli import app

def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "AI mini box" in result.output

def test_cli_no_args_shows_help():
    runner = CliRunner()
    result = runner.invoke(app, [])
    assert result.exit_code == 0
```

## Требования к каждому сервису

При создании нового сервиса (отдельный пакет `ai-mini-box-{name}`):

1. **Файл сервиса** помещается в `ai_mini_box/tools/{name}.py`
2. **pyproject.toml** сервиса указывает зависимость: `"ai-mini-box-core>=4.0"`
3. **Функция `register(app: typer.Typer)`** в каждом файле сервиса — единственная точка подключения
4. **Тесты:** unit (с MockRepo) + интеграционные (с CliRunner) + smoke (регистрация в CLI)
5. **Импорты:** только из `ai_mini_box.core` и `ai_mini_box.infrastructure`. Запрещено импортировать другие сервисы

## Тестирование

В каждом spec-файле сервиса должен быть раздел «Тесты» с указанием:

1. **Unit-тесты** — какие MockRepo использовать, какие кейсы покрыть
2. **Интеграционные тесты** — какие фикстуры из conftest использовать
3. **Пример кода теста** — готовый шаблон

Уровни тестов:
- `tests/test_{service}.py` — unit (isolation)
- `tests/integration/test_{service}.py` — integration (with framework)
- `tests/smoke/` — smoke (CLI registration)
