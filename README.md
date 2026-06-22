# AI mini box

[![CI](https://github.com/Kibertum/ai-mini-box/actions/workflows/tests.yml/badge.svg)](https://github.com/Kibertum/ai-mini-box/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/ai-mini-box-core)](https://pypi.org/project/ai-mini-box-core/)
[![Python](https://img.shields.io/pypi/pyversions/ai-mini-box-core)](https://pypi.org/project/ai-mini-box-core/)
[![License](https://img.shields.io/github/license/Kibertum/ai-mini-box)](LICENSE)

Системное ядро для автоматизации малого бизнеса. Управление контактами, продуктами, заказами, сообщениями через единый CLI и плагинную систему сервисов.

## Установка

```bash
pip install ai-mini-box-core
```

Для разработки — с тестовыми зависимостями:

```bash
git clone https://github.com/Kibertum/ai-mini-box
cd ai-mini-box
pip install -e packages/core[dev]
pip install -e packages/demo[dev]    # пример сервиса
```

## Быстрый старт

```bash
# Инициализация проекта
ai-mini-box init

# Проверка БД
ai-mini-box check-db

# Настройка
ai-mini-box config show
ai-mini-box config set telegram_bot_token "your_token"
ai-mini-box config set poll_interval 15
ai-mini-box config unset poll_interval
```

## Команды CLI

| Команда | Описание |
|---------|----------|
| `init` | Создать config.json, БД, директории data/ |
| `check-db` | Проверить подключение к БД и схему |
| `db upgrade` | Применить миграции БД (Alembic) |
| `config list` | Показать все доступные ключи с типами и дефолтами |
| `config show` | Показать конфигурацию (с группировкой по секциям) |
| `config set <key> <value>` | Установить значение (чувствительные поля шифруются) |
| `config unset <key>` | Сбросить на значение по умолчанию |

Плагины (сервисы) регистрируют свои команды через entry points:

| Команда (из demo) | Описание |
|---|---|
| `demo-list` | Список контактов |
| `demo-get <id>` | Контакт по ID |
| `demo-add <name> <phone>` | Добавить контакт |

Опции: `--verbose`, `--log-file <path>`, `--help` доступны для всех команд. Автодополнение: `ai-mini-box --install-completion`.

## Архитектура

```
ai_mini_box/
├── core/                  # Слой домена
│   ├── models.py          # Pydantic-модели (Contact, Product, Message, Order)
│   ├── repositories.py    # ABC репозиториев + QueryBuilder
│   ├── container.py       # RepoContainer + AppContext (DI)
│   └── exceptions.py      # Кастомные исключения
├── infrastructure/        # Слой инфраструктуры
│   ├── database.py        # SQLAlchemy engine, session, get_db()
│   ├── config.py          # JsonConfigManager с шифрованием
│   ├── logger.py          # Loguru-логгер
│   ├── orm_models.py      # SQLAlchemy ORM-модели
│   ├── mapping.py         # Мапперы Pydantic ↔ ORM
│   └── repositories/      # SQLAlchemy-реализации репозиториев
└── cli.py                 # Typer CLI + плагинная загрузка
```

**Слои:** `core/` (Pydantic + ABC) → `infrastructure/` (SQLAlchemy + файлы) → `tools/` (CLI-сервисы через entry points).

## Разработка сервиса

См. [docs/developer-guide.md](docs/developer-guide.md).

## Сервисы (инструменты)

Проект включает 30 спецификаций сервисов в `tool-*.md` — от телеграм-бота и email до CRM-синхронизации и юристов. Каждый сервис — отдельный Python-пакет, подключаемый через entry point `ai_mini_box.tools`.

## Тестирование

```bash
pytest packages/core/tests/ packages/demo/tests/ -v
```

Текущий статус: **72 теста, все зелёные** (63 core + 9 demo).

## Лицензия

MIT
