# Промпт: Реализация ai-mini-box-core

## Описание

Реализовать базовый пакет `ai-mini-box-core` — каркас для системы CLI-инструментов автоматизации малого бизнеса. Core — единственный обязательный пакет, все остальные сервисы подключаются как отдельные pip-пакеты (entry points `ai_mini_box.tools`) и автоматически регистрируются в CLI.

**Текущая версия:** 5.0.1

## Технологии

- Python 3.12+
- Typer — CLI-фреймворк
- SQLAlchemy 2.0 (синхронный) — ORM
- Pydantic v2 — модели данных (вместо dataclass'ов)
- Alembic — миграции БД
- loguru — логирование
- cryptography (Fernet) — шифрование sensitive полей конфига
- pytest — тестирование

## Структура пакета

```
ai-mini-box-core/
├── pyproject.toml
├── alembic.ini
├── data/
│   └── config.json          # конфиг по умолчанию (runtime — data/config.json корня)
├── logs/
├── migrations/               # внешние миграции (alembic.ini)
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── ab2eb6df34f5_initial_models.py
│       ├── d9a1b2c3e4f5_add_tasks_table.py
│       └── e6f5a4b3c2d1_add_knowledge_base_and_extracted_fields.py
├── ai_mini_box/
│   ├── __init__.py
│   ├── __main__.py                   # python -m ai_mini_box → cli.app()
│   ├── cli.py                        # главная Typer-группа + entry point plugin loader
│   ├── testing.py                    # _MemoryStore + Mock*Repo для unit-тестов сервисов
│   │
│   ├── core/                         # ★ Абстракции (не зависят от БД)
│   │   ├── __init__.py
│   │   ├── models.py                 # Pydantic v2 модели всех сущностей
│   │   ├── repositories.py           # ABC репозиториев + QueryBuilder
│   │   ├── container.py              # RepoContainer (DI) + AppContext (синглтон)
│   │   ├── exceptions.py             # кастомные исключения
│   │   ├── classifier.py             # Classifier ABC + KeywordClassifier + create_classifier()
│   │   ├── classifier_llm.py         # LlmCppClassifier (llama_cpp)
│   │   ├── extraction.py             # extract_phone() — регулярка для номеров
│   │   └── answer_service.py         # auto_draft_response() — KB matching + LLM placeholder
│   │
│   ├── infrastructure/               # ★ Реализации (SQLAlchemy, JSON, etc.)
│   │   ├── __init__.py
│   │   ├── database.py               # engine, sessionmaker, init_db(), get_db(), get_db_path()
│   │   ├── config.py                 # AppConfig (Pydantic, 30 полей) + JsonConfigManager (Fernet)
│   │   ├── logger.py                 # настройка loguru
│   │   ├── orm_models.py             # SQLAlchemy ORM модели (6 таблиц)
│   │   ├── mapping.py                # Pydantic ↔ ORM конвертеры
│   │   ├── migrations/               # внутренние миграции (для CLI db upgrade)
│   │   │   ├── env.py
│   │   │   ├── script.py.mako
│   │   │   └── versions/             # те же revision'ы, что во внешних
│   │   └── repositories/             # SQLAlchemy реализации
│   │       ├── __init__.py
│   │       ├── contact_repo.py
│   │       ├── product_repo.py
│   │       ├── message_repo.py
│   │       ├── order_repo.py
│   │       ├── task_repo.py
│   │       └── kb_repo.py
│   │
│   ├── tools/                        # ★ Точка подключения сервисов
│   │   └── __init__.py               # пустой, entry points приземляются сюда
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py               # общие фикстуры
│       ├── test_registry.py          # smoke-тест CLI
│       ├── unit/
│       │   ├── test_logger.py
│       │   └── test_config.py
│       └── integration/
│           ├── __init__.py
│           ├── conftest.py           # in-memory SQLite engine
│           ├── test_contact_repo.py
│           ├── test_product_repo.py
│           ├── test_message_repo.py
│           ├── test_order_repo.py
│           ├── test_cli_init.py
│           ├── test_cli_db.py
│           ├── test_cli_config_list.py
│           └── test_config_cli.py
```

## Детальная реализация

### 1. pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ai-mini-box-core"
version = "5.0.1"
description = "AI mini box core — system core for small business automation"
requires-python = ">=3.12"
dependencies = [
    "typer>=0.12",
    "SQLAlchemy>=2.0",
    "loguru>=0.7",
    "pydantic>=2.0",
    "alembic>=1.13",
    "cryptography>=42",
]
[project.optional-dependencies]
dev = ["pytest>=8", "pytest-xdist>=3", "pytest-cov>=5"]
[project.scripts]
ai-mini-box = "ai_mini_box.cli:app"

[tool.hatch.build]
include = ["ai_mini_box/**"]
```

### 2. cli.py — главная точка входа

```python
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
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    log_file: str = typer.Option(None, "--log-file"),
):
    if verbose:
        os.environ["AI_BOX_VERBOSE"] = "1"
    from ai_mini_box.infrastructure.logger import setup_logging
    setup_logging(verbose=verbose, log_file=Path(log_file) if log_file else None)

# sub-typers: config, db
config_app = typer.Typer(help="Manage configuration")
app.add_typer(config_app, name="config")
db_app = typer.Typer(help="Database management")
app.add_typer(db_app, name="db")

@app.command()
def init(force=False, config_path="data/config.json", db_path="data/app.db"):
    """Initialize project: create config, database, directories."""
    # создаёт data/{backup,models,training}
    # создаёт config.json через JsonConfigManager
    # init_db(db_path) + _run_migrations(db_path) — schema через alembic
    ...

def _run_migrations(db_path: Path | None = None):
    """Выполняет alembic upgrade head."""
    # читает AI_BOX_DB_PATH из env если есть
    # находит migrations/ рядом с __file__
    # запускает command.upgrade()

@db_app.command()
def upgrade():
    _run_migrations()

# config list/show/set/unset — CRUD конфига с типизацией
# config show — группировка по секциям (Telegram, Email, LLM...)
# config set — type coercion (int, bool, list[int])
# sensitive fields маскируются при выводе

# Plugin loader — в конце файла:
for ep in importlib.metadata.entry_points(group="ai_mini_box.tools"):
    try:
        register_func = ep.load()
        if callable(register_func):
            register_func(app)
    except Exception as e:
        typer.echo(f"Warning: failed to load tool {ep.name}: {e}", err=True)
```

**Важно:** каждый сервис экспортирует функцию `register(app: typer.Typer)`, которая добавляет свою подгруппу команд через entry point `ai_mini_box.tools`. Никакой ручной регистрации в cli.py не требуется.

### 3. core/models.py — Pydantic v2 модели

```python
from datetime import date, datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class Topic(str, Enum):
    PRICES = "Цены"          # русские значения для UI
    ORDER = "Заказ"
    COMPLAINT = "Жалоба"
    SCHEDULE = "График"
    OTHER = "Другое"

class MessageSource(str, Enum): TELEGRAM, EMAIL, WHATSAPP, SMS, MANUAL
class OrderStatus(str, Enum): NEW, PROCESSING, COMPLETED, CANCELLED
class TaskPriority(str, Enum): LOW, MEDIUM, HIGH

class Contact(BaseModel):
    id: Optional[int] = None
    name: str = ""
    phone: Optional[str] = None
    email: Optional[str] = None
    telegram: Optional[str] = None
    whatsapp: Optional[str] = None
    source: MessageSource = MessageSource.MANUAL
    notes: Optional[str] = None
    total_spent: int = 0  # в копейках
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Product(BaseModel): ...
class Message(BaseModel):
    # +extracted_phone: Optional[str], extracted_name: Optional[str]
    ...
class Task(BaseModel):
    id: Optional[int] = None
    title: str = ""
    description: Optional[str] = None
    due_date: date = Field(default_factory=date.today)
    due_time: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: str = "pending"
    contact_id: Optional[int] = None
    assignee: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Order(BaseModel): ...
class KnowledgeBaseItem(BaseModel):
    id: Optional[int] = None
    topic: Optional[Topic] = None
    question_keywords: list[str] = Field(default_factory=list)
    answer_text: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

### 4. core/repositories.py — ABC репозиториев + QueryBuilder

- **QueryBuilder** — chainable: `.filter(**kwargs).search(query, *fields).sort(key).limit(n).offset(n).all()/.first()/.count()`
- **ContactRepo, ProductRepo, MessageRepo, OrderRepo, TaskRepo, KnowledgeBaseRepo** — ABC с `query()`, `list()`, `get_by_id()`, `add()`, `update()`, `delete()` + entity-specific методы (search, find_matching, search_by_topic)

### 5. core/container.py — DI

```python
class RepoContainer:
    def __init__(self, session: Session):
        self.contacts = SqliteContactRepo(session)
        self.products = SqliteProductRepo(session)
        self.messages = SqliteMessageRepo(session)
        self.orders = SqliteOrderRepo(session)
        self.tasks = SqliteTaskRepo(session)
        self.kb = SqliteKnowledgeBaseRepo(session)

class AppContext:
    repos: RepoContainer
    config_path: str
    verbose: bool
    _instance: Optional["AppContext"] = None

    @classmethod
    def init(cls, repos, **kwargs) -> "AppContext": ...
    @classmethod
    def get(cls) -> "AppContext": ...
```

### 6. core/exceptions.py

```python
class AppError(Exception):      # exit_code=1
class NotFoundError(AppError):   # exit_code=2
class ConfigError(AppError):     # exit_code=3
```

### 7. core/classifier.py — классификация тем

```python
class Classifier(ABC):
    def classify(self, text: str) -> Topic: ...

class KeywordClassifier(Classifier):
    # regex-правила: цена/стоит/руб → Topic.PRICES, заказ/купи → ORDER, ...
    # fallback → Topic.OTHER

def create_classifier() -> Classifier:
    # если установлен llama_cpp → LlmCppClassifier, иначе → KeywordClassifier
    ...
```

### 8. core/classifier_llm.py — LLM-классификатор

```python
class LlmCppClassifier(Classifier):
    # загружает GGUF модель из config.llm_model_path
    # запускает prompt на классификацию
    # парсит ответ в Topic
```

### 9. core/extraction.py — извлечение сущностей

```python
PHONE_RE = re.compile(r"\+?[\d][\d\s\-\(\)]{5,15}[\d]")

def extract_phone(text: str) -> Optional[str]:
    """Извлекает первый номер телефона из текста (7-15 цифр)."""
    ...
```

### 10. core/answer_service.py — автоподготовка ответа

```python
def auto_draft_response(text: str, topic: Topic, repos: RepoContainer) -> Optional[str]:
    """
    Layer 1: KnowledgeBase keyword matching (set intersection) — MVP
    Layer 2: LLM-generation — future
    """
    matches = repos.kb.find_matching(text, topic)
    return matches[0].answer_text if matches else None
```

### 11. infrastructure/database.py

```python
from contextlib import contextmanager

class Base(DeclarativeBase): pass

# Глобальные синглтоны: _engine, _SessionLocal

def get_db_path() -> Path:
    # читает AI_BOX_DB_PATH env var, иначе data/app.db

def init_db(db_path=None):
    # создаёт engine + sessionmaker
    # НЕ вызывает create_all — схема только через alembic

def get_engine(): ...
def get_session(): ...
@contextmanager
def get_db() -> Generator[Session, None, None]:
    # commit/rollback/close

def dispose_engine(): ...
```

### 12. infrastructure/config.py — Pydantic + Fernet

```python
SENSITIVE_FIELDS = frozenset({
    "email_password", "telegram_token", "whatsapp_api_key",
    "sms_api_key", "sms_api_secret", "yookassa_secret_key",
    "tinkoff_password", "sber_password",
})

class AppConfig(BaseModel):
    # 30 полей: Telegram (token, bot_name, allowed_chat_ids),
    # Email (imap_server/port, login, password),
    # LLM (model_path, n_ctx, n_threads),
    # WhatsApp, SMS, YooKassa, Tinkoff, Sber,
    # Schedule, Notifications, General (poll_interval...)
    class Config:
        env_prefix = "AI_BOX_"

class JsonConfigManager:
    def __init__(self, path="data/config.json"): ...
    def load(self) -> AppConfig:
        # читает JSON, расшифровывает SENSITIVE_FIELDS через Fernet
        # применяет AI_BOX_* env overrides
    def save(self, config: AppConfig):
        # шифрует sensitive поля, пишет JSON
    def set(self, key, value):
        # type coercion: int, bool, list[int]
    def unset(self, key):
        # удаляет из JSON, восстанавливая default
```

Ключ Fernet выводится из `AI_BOX_SECRET` env var (PBKDF2HMAC, SHA-256, 480k итераций).

### 13. infrastructure/orm_models.py — SQLAlchemy ORM модели

6 моделей (все наследуют `Base`):
- `ContactModel` → `contacts`
- `ProductModel` → `products`
- `MessageModel` → `messages` (+ extracted_phone, extracted_name)
- `TaskModel` → `tasks`
- `OrderModel` → `orders`
- `KnowledgeBaseModel` → `knowledge_base` (question_keywords: Text с JSON)

### 14. infrastructure/mapping.py — Pydantic ↔ ORM

Пары функций на каждую модель:
- `contact_to_orm(contact: Contact) -> ContactModel`
- `contact_from_orm(model: ContactModel) -> Contact`
- `kb_item_to_orm(item: KnowledgeBaseItem) -> KnowledgeBaseModel` (json.dumps для keywords)
- `kb_item_from_orm(model: KnowledgeBaseModel) -> KnowledgeBaseItem` (json.loads для keywords)

### 15. testing.py — Mock-репозитории

```python
class _MemoryStore:
    # dict[int, object] + autoincrement id
    # query/get/add/update/delete

class MockContactRepo(ContactRepo):
    def __init__(self):
        self._store = _MemoryStore()
    # делегирует _MemoryStore + search через QueryBuilder

class MockProductRepo(ProductRepo): ...
class MockMessageRepo(MessageRepo): ...
class MockOrderRepo(OrderRepo): ...
class MockKnowledgeBaseRepo(KnowledgeBaseRepo):
    # find_matching: set intersection scoring (как SqliteKBRepo)
```

### 16. Миграции (Alembic)

3 миграции:

| Revision | Parent | Описание |
|---|---|---|
| `ab2eb6df34f5` | — | Initial: contacts, messages, orders, products |
| `d9a1b2c3e4f5` | `ab2eb6df34f5` | Add tasks table |
| `e6f5a4b3c2d1` | `d9a1b2c3e4f5` | Add knowledge_base, extracted_phone/name on messages |

`env.py` читает `AI_BOX_DB_PATH` для переопределения пути к БД.

**Важно:** внутренние `ai_mini_box/migrations/` и внешние `migrations/` содержат одинаковые revisions. CLI `db upgrade` использует внутренние.

## Требования к каждому сервису

При создании нового сервиса (отдельный пакет `ai-mini-box-{name}`):

1. **Entry point** в `pyproject.toml` сервиса:
   ```toml
   [project.entry-points."ai_mini_box.tools"]
   {name} = "ai_mini_box_{name}.commands:register"
   ```
2. **pyproject.toml** сервиса указывает зависимость: `"ai-mini-box-core>=5.0"`
3. **Функция `register(app: typer.Typer)`** — единственная точка подключения (принимает Typer, добавляет команды)
4. **Тесты:** unit (с MockRepo из `ai_mini_box.testing`) + интеграционные (с CliRunner) + smoke (регистрация в CLI)
5. **Импорты:** только из `ai_mini_box.core` и `ai_mini_box.infrastructure`. Запрещено импортировать другие сервисы
6. **Для работы с репозиториями:** использовать `RepoContainer` (брать через `AppContext.get().repos`)

## Тестирование

В каждом spec-файле сервиса должен быть раздел «Тесты» с указанием:

1. **Unit-тесты** — какие MockRepo из `ai_mini_box.testing` использовать, какие кейсы покрыть
2. **Интеграционные тесты** — in-memory SQLite через `db_engine`/`db_session` фикстуры из `integration/conftest.py`
3. **Пример кода теста** — готовый шаблон

Уровни тестов:
- `tests/test_{service}.py` — unit (isolation, MockRepo)
- `tests/integration/test_{service}.py` — integration (SQLAlchemy + in-memory)
- `tests/smoke/` — smoke (CLI registration)
