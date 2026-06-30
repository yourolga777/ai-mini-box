# Отчёт: core-пакет (ai-mini-box-core)

**Дата:** 27.06.2026  
**Ветка:** main  
**Тестов:** 87 / 87 пройдено

---

## 1. Архитектура

```
ai_mini_box/
├── __init__.py          # пакет
├── __main__.py          # точка входа python -m
├── cli.py               # Typer CLI: init, config, db, plugin
├── testing.py           # моки для тестов плагинов
│
├── core/
│   ├── models.py        # Pydantic-модели (Contact, Message, Order, OrderItem, ...)
│   ├── repositories.py  # ABC репозиториев (interfaces)
│   ├── container.py     # DI-контейнер RepoContainer (7 репозиториев)
│   ├── exceptions.py    # кастомные исключения
│   ├── classifier.py    # классификатор сообщений
│   ├── classifier_llm.py# LLM-классификатор
│   ├── answer_service.py# сервис ответов
│   ├── extraction.py    # извлечение сущностей
│   │
│   └── services/
│       ├── __init__.py
│       ├── registry.py  # PluginRegistry (service provider)
│       ├── llm.py       # LLMService
│       └── plugin_catalog.py  # PluginCatalog
│
├── infrastructure/
│   ├── config.py        # JsonConfigManager + AppConfig (Pydantic)
│   ├── database.py      # SQLAlchemy engine, session, init_db, PRAGMA FK
│   ├── orm_models.py    # ORM-модели (Mapped-стиль)
│   ├── mapping.py       # маппинг Pydantic ↔ ORM
│   ├── logger.py        # настройка логирования
│   │
│   └── repositories/
│       ├── __init__.py
│       ├── contact_repo.py
│       ├── message_repo.py
│       ├── product_repo.py
│       ├── order_repo.py     # + SqliteOrderItemRepo
│       ├── task_repo.py
│       └── kb_repo.py
│
├── data/
│   └── plugin-catalog.json   # встроенный каталог плагинов
│
└── migrations/
    ├── env.py
    └── versions/
        ├── ab2eb6df34f5_initial_models.py
        ├── d9a1b2c3e4f5_add_tasks_table.py
        ├── e6f5a4b3c2d1_add_knowledge_base_and_extracted_fields.py
        ├── f7a8b9c0d1e2_add_extracted_order_id.py
        └── a1b2c3d4e5f6_add_order_items_table.py
```

---

## 2. Модели (Pydantic + ORM)

| Модель | Pydantic | ORM (Mapped) | Маппинг |
|---|---|---|---|
| Contact | `core/models.py:Contact` | `ContactModel` | `mapping.py` |
| Message | `core/models.py:Message` | `MessageModel` | `mapping.py` |
| Product | `core/models.py:Product` | `ProductModel` | `mapping.py` |
| Order | `core/models.py:Order` | `OrderModel` | `mapping.py` |
| **OrderItem** | `core/models.py:OrderItem` | `OrderItemModel` | `mapping.py` |
| Task | `core/models.py:Task` | `TaskModel` | `mapping.py` |
| KnowledgeBase | `core/models.py:KnowledgeBase` | `KnowledgeBaseModel` | `mapping.py` |
| LlmCategory | `core/models.py:LlmCategory` | — | — |
| Folder | `core/models.py:Folder` | — | — |

### OrderItem (добавлено в этой сессии)

```python
class OrderItem(BaseModel):
    id: int = 0
    order_id: int
    product_id: int
    product_name: str
    quantity: int = 1
    price: Decimal = Decimal("0.00")
    total: Decimal = Decimal("0.00")
```

- `total` вычисляется: `quantity * price`
- `_recalc_total()` в `SqliteOrderItemRepo` — пересчёт суммы заказа при add/update/delete OrderItem
- CASCADE при удалении Order

---

## 3. CLI-команды

| Команда | Описание |
|---|---|
| `ai-mini-box init` | Инициализация проекта: создание data/, БД, миграции |
| `ai-mini-box db upgrade` | Применить миграции |
| `ai-mini-box config list` | Список ключей с типами и значениями по умолчанию |
| `ai-mini-box config show` | Показать текущий конфиг |
| `ai-mini-box config set <key> <value>` | Установить значение (sensitive → шифруется) |
| `ai-mini-box config unset <key>` | Сбросить на default |
| `ai-mini-box plugin catalog` | Показать каталог плагинов |
| `ai-mini-box plugin refresh` | Обновить кеш каталога |

---

## 4. JsonConfigManager

- 30 полей конфига (AppConfig), 3 секции: `[general]`, `[llm]`, `[telegram]`
- Чтение: `data/config.json`
- Шифрование: `sensitive_fields` шифруются через `cryptography.fernet`
- **Race condition fix**: `threading.Lock` + атомарная запись `os.replace()` (tmp-файл) + `_decrypt()` fallback
- **Предупреждение**: PydanticDeprecatedSince20 — `class Config` устарел, нужен `model_config`

---

## 5. PluginCatalog

- Встроенный JSON: `data/plugin-catalog.json`
- Класс `PluginCatalog`: `sync()` / `load()` / `get_status()`
- `sync()` мержит builtin + кастомные записи (по уникальному имени)
- Вызов `sync()` при `init`
- CLI: `plugin catalog`, `plugin refresh`

```json
[
  {"name": "demo", "version": "0.1.0", "description": "...", "status": "builtin"},
  {"name": "telegram", "version": "0.1.0", "description": "...", "status": "builtin"},
  {"name": "web", "version": "0.1.0", "description": "...", "status": "builtin"}
]
```

---

## 6. Репозитории (7 шт.)

| Репозиторий | Методы |
|---|---|
| ContactRepo | add, get_by_id, update, delete, list (filter, pagination), search |
| MessageRepo | add, get_by_id, list (filter), search (topic) |
| ProductRepo | add, get_by_id, update, delete, search, list (filter, pagination) |
| OrderRepo | add, get_by_id, update_status, list (filter, pagination) |
| **OrderItemRepo** | **add, get_by_id, update, delete, list_by_order, _recalc_total** |
| TaskRepo | add, list |
| KbRepo | add, get_by_id, update, delete, search |

Все: ABC → Sqlite имплементация.

---

## 7. База данных

- **Engine**: SQLite через SQLAlchemy + NullPool
- **PRAGMA foreign_keys=ON**: включена через `event.listen` при `init_db()`
- **Миграции**: Alembic, 5 ревизий (цепочек)
- Head: `a1b2c3d4e5f6` (add_order_items_table)

### Миграции

| Ревизия | Родитель | Описание |
|---|---|---|
| `ab2eb6df34f5` | — | Initial: contacts, messages, products, orders, llm_categories |
| `d9a1b2c3e4f5` | `ab2eb6df34f5` | add_tasks_table |
| `e6f5a4b3c2d1` | `d9a1b2c3e4f5` | add_knowledge_base_and_extracted_fields |
| `f7a8b9c0d1e2` | `e6f5a4b3c2d1` | add_extracted_order_id (batch mode + named FK) |
| `a1b2c3d4e5f6` | `f7a8b9c0d1e2` | add_order_items_table |

Две директории синхронизированы: `migrations/` и `ai_mini_box/migrations/`.

---

## 8. DI-контейнер

```python
class RepoContainer:
    def __init__(self, session: Session):
        self.contacts = SqliteContactRepo(session)
        self.messages = SqliteMessageRepo(session)
        self.products = SqliteProductRepo(session)
        self.orders = SqliteOrderRepo(session)
        self.order_items = SqliteOrderItemRepo(session)
        self.tasks = SqliteTaskRepo(session)
        self.kb = SqliteKbRepo(session)
```

Тестовый мок: `MockRepoContainer` в `testing.py`.

---

## 9. Тесты

```
tests/
├── integration/
│   ├── test_cli_config_list.py   — 3 теста
│   ├── test_cli_db.py             — 1 тест
│   ├── test_cli_init.py           — 4 теста
│   ├── test_config_cli.py         — 10 тестов
│   ├── test_contact_repo.py       — 11 тестов
│   ├── test_message_repo.py       — 7 тестов
│   ├── test_order_item_repo.py    — 13 тестов (NEW)
│   ├── test_order_repo.py         — 8 тестов
│   └── test_product_repo.py       — 10 тестов
├── test_registry.py               — 1 тест
└── unit/
    ├── test_config.py             — 16 тестов
    └── test_logger.py             — 3 теста
```

**Итого: 87 тестов, 87 passed.**

### Покрытие OrderItem (13 тестов)
- `test_add` — создание OrderItem
- `test_list_by_order` — список по заказу
- `test_list_by_order_empty` — пустой список
- `test_get_by_id` — получение по ID
- `test_get_by_id_not_found` — 404
- `test_update` — обновление
- `test_update_not_found` — 404
- `test_delete` — удаление
- `test_delete_not_found` — 404
- `test_recalc_total_on_add` — пересчёт суммы заказа при добавлении
- `test_recalc_total_on_delete` — пересчёт при удалении
- `test_recalc_total_on_update` — пересчёт при обновлении
- `test_cascade_delete` — CASCADE при удалении заказа

### conftest особенности
- `PRAGMA foreign_keys=ON` включена через событие `connect`
- `Base.metadata.create_all()` перед тестами
- Фикстура `session` — транзакция с откатом

---

## 10. PluginRegistry (service provider)

- Плагины регистрируются через `PluginRegistry.register()`
- Плагины НЕ импортируют друг друга, общаются через registry
- `PluginRegistry.get_service()` / `get_services_by_interface()`
- `PluginRegistry.get_plugins()` — список зарегистрированных

---

## 11. Известные проблемы

| Проблема | Статус |
|---|---|
| `AppConfig` — PydanticDeprecatedSince20 (`class Config` → `model_config`) | Warning, не блокирует |
| `ai_mini_box_llm` плагин: `no such column: llm_categories.order` | LLM-таблицы не обновлены |
| Внешние тесты (`test_api_contacts.py`) — `create_all` не вызывается | Не входит в core |

---

## 12. Ключевые решения (приняты в этой сессии)

1. **OrderItem — только `list_by_order()`**: без `list()`/`search()`, CASCADE при удалении Order
2. **PluginCatalog — только builtin JSON**: без GitHub, PR в репозиторий core для новых плагинов
3. **ORM-стиль**: `Mapped`/`mapped_column` (современный SQLAlchemy 2.0)
4. **`_recalc_total` — метод репозитория**: не модульная функция
5. **Миграции на SQLite — batch mode**: обязателен для FK через `op.batch_alter_table()`
6. **PRAGMA foreign_keys=ON глобально**: через `event.listen`, иначе CASCADE не работает в тестах
