# AI mini box 4.0 — Спецификация пакета инструментов

## Обзор

Редизайн архитектуры: вместо монолитного приложения — **пакет CLI-инструментов**. Ядро (`ai-mini-box-core`) — каркас с БД, конфигом и CLI. Все сервисы — отдельные pip-пакеты, которые автоматически регистрируются в общем CLI.

```bash
pip install ai-mini-box-core              # каркас (обязательно)
pip install ai-mini-box-contacts           # доп. сервисы по выбору
pip install ai-mini-box-products
# ...
ai-mini-box --help  # все установленные сервисы видны автоматически
```

## Все сервисы

### 🟢 База (ядро)

| Инструмент | Описание | Сложность | Важность |
|---|---|---|---|
| `init` | Создание config.json, БД и директорий при первом запуске | Easy | Critical |
| `config` | Управление конфигурацией (show/get/set/check/reset) | Easy | Critical |
| `search` | Полнотекстовый поиск по сообщениям, контактам, товарам | Easy | High |

### 🟢 CRM + Товары

| Инструмент | Описание | Сложность | Важность |
|---|---|---|---|
| `contacts` | CRUD контактов + импорт/экспорт CSV/JSON | Easy | Critical |
| `products` | CRUD товаров + импорт/экспорт | Easy | Critical |
| `orders` | Заказы: создание, статусы, история, связь с контактами | Medium | Critical |
| `loyalty` | Бонусы и скидки постоянным клиентам | Medium | Medium |

### 🟡 Каналы связи

| Инструмент | Описание | Сложность | Важность |
|---|---|---|---|
| `telegram` | Telegram-канал (test/poll/send/webhook) | Medium | Critical |
| `email` | Email-канал (test/poll/send) | Medium | High |
| `whatsapp` | WhatsApp-канал (test/poll/send) | Hard | Critical |
| `sms` | SMS-канал (test/send/config) | Medium | Nice-to-have |

### 🔴 Умные функции

| Инструмент | Описание | Сложность | Важность |
|---|---|---|---|
| `classify` | Классификация текста по 5 темам | Easy | Critical |
| `train` | Дообучение классификатора на своих примерах | Medium | High |
| `draft` | Генерация черновика ответа через LLM | Medium | High |
| `lawyer` | RAG-юрист (вопросы по законам) | Medium | Medium |
| `ingest-laws` | Загрузка законов в RAG-индекс | Medium | Medium |

### 🔴 Демон + Уведомления

| Инструмент | Описание | Сложность | Важность |
|---|---|---|---|
| `serve` | Фоновый демон обработки сообщений | Hard | Critical |
| `notify` | Уведомления владельца о событиях | Easy | High |

### 🟢 Отчёты + Утилиты

| Инструмент | Описание | Сложность | Важность |
|---|---|---|---|
| `report` | Отчёты и статистика (topics/timeline/export) | Easy | High |
| `backup` | Резервное копирование БД | Easy | High |
| `analytics` | LTV, retention, конверсия, прогнозы | Medium | Medium |

### 🟣 Веб + GUI

| Инструмент | Описание | Сложность | Важность |
|---|---|---|---|
| `web` | Веб-интерфейс (FastAPI, браузер) | Hard | Critical |
| `gui` | Десктопный PyQt6 интерфейс | Easy | Nice-to-have |

### 🟠 Доп. бизнес-инструменты

| Инструмент | Описание | Сложность | Важность |
|---|---|---|---|
| `invoices` | Создание счетов/чеков в PDF, отправка клиенту | Medium | High |
| `calendar` | Запись на услуги, расписание | Medium | Medium |
| `survey` | Опросы и NPS | Easy | Medium |
| `tasks` | Внутренние задачи и напоминания | Medium | Medium |

### 🟤 Интеграции

| Инструмент | Описание | Сложность | Важность |
|---|---|---|---|
| `import-wb` | Импорт заказов/товаров с Wildberries, Ozon, Я.Маркет | Hard | High |
| `payment` | Приём платежей (ЮКасса, Tinkoff, Сбер) | Hard | High |
| `crm-sync` | Синхронизация с AmoCRM, Bitrix24 | Medium | Medium |

## Структура пакетов

```
ai-mini-box-core/                     # публикуется в PyPI
├── pyproject.toml                    # зависимости: typer, SQLAlchemy, loguru
└── ai_mini_box/
    ├── __init__.py
    ├── __main__.py                   # python -m ai_mini_box
    ├── cli.py                        # Typer app + авто-поиск tools/
    ├── core/
    │   ├── models.py                 # Contact, Product, Message, Order, Topic, ...
    │   ├── repositories.py           # ABC: ContactRepo, ProductRepo, MessageRepo, ...
    │   └── exceptions.py             # AppError, NotFoundError, ConfigError
    ├── infrastructure/
    │   ├── database.py               # engine, session, init_db()
    │   ├── config.py                 # JsonConfigManager
    │   ├── logger.py                 # loguru setup
    │   └── repositories/             # SQLAlchemy реализации
    ├── tools/
    │   └── __init__.py               # пустой (namespace package)
    └── tests/
        ├── conftest.py               # фикстуры: CliRunner, tmp_config, mock_repos
        ├── mocks.py                  # MockContactRepo, MockProductRepo, ...
        └── test_registry.py          # smoke: проверка регистрации команд

ai-mini-box-contacts/                 # отдельный пакет
├── pyproject.toml                    # depends: ai-mini-box-core
└── ai_mini_box/tools/
    └── contacts.py                   # регистрируется в CLI автоматически

ai-mini-box-products/                 # отдельный пакет
├── pyproject.toml
└── ai_mini_box/tools/
    └── products.py
```

## Зависимости (pyproject.toml core)

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
[project.optional-dependencies]
dev = ["pytest>=8", "pytest-cov>=5"]
[project.scripts]
ai-mini-box = "ai_mini_box.cli:app"
```

## Рекомендуемый порядок реализации

| Этап | Сервисы | Результат |
|------|---------|-----------|
| **MVP** | core + init + config + contacts + products + search + telegram + whatsapp + classify + serve + notify + web | Рабочий продукт для продажи |
| **2** | orders + draft + email + report + backup + invoices | Полный цикл продаж |
| **3** | lawyer + ingest-laws + train + analytics + calendar + survey + tasks | Умные функции |
| **4** | loyalty + import-wb + payment + crm-sync + sms + gui | Интеграции и ниши |

## Тестирование

Каждый сервис тестируется на 3 уровнях (подробнее в `Тесты.md`):

1. **Unit** — mock-репозитории, изолированная логика
2. **Integration** — CliRunner + тестовая БД
3. **Smoke** — `ai-mini-box --help` показывает все команды

CI перед мержем прогоняет тесты ВСЕХ сервисов (`pytest tests/`).
