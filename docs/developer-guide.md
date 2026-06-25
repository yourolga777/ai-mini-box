# Руководство разработчика

## Для кого этот документ

В проекте две роли. Выбери свою:

| Ты | Читать |
|---|---|
| Разрабатываешь **плагин** (LLM, Telegram, WhatsApp...) | → `plugin-developer-prompt.md` |
| Разрабатываешь **каркас** (core) | → `core-developer-prompt.md` |

## Документация

### Для плагинов

| Файл | О чём |
|---|---|
| `plugin-developer-prompt.md` | Системный промпт — начать здесь |
| `plugin-template.md` | Пошаговый шаблон для быстрого старта |
| `plugins/00-overview.md` | Общий обзор плагинной системы |
| `plugins/01-package-setup.md` | Настройка pyproject.toml |
| `plugins/02-cli-entry-point.md` | CLI-команды и демоны |
| `plugins/03-database.md` | БД, репозитории, QueryBuilder |
| `plugins/04-config.md` | Конфиг и env-переменные |
| `plugins/05-help.md` | Help-секции для веб-интерфейса |
| `plugins/06-testing.md` | Unit и интеграционные тесты |
| `plugins/07-publishing.md` | Публикация на PyPI |
| `plugins/08-example.md` | Полный пример готового плагина |
| `plugins/09-web-management.md` | Web UI: установка, управление демонами |
| `plugins/10-service-registry.md` | Регистрация сервисов для других плагинов |
| `plugins/11-llm-plugin.md` | Спецификация для разработчика LLM-плагина |
| `plugins/12-telegram-plugin.md` | Telegram-specific patterns (справочно) |

### Для каркаса

| Файл | О чём |
|---|---|
| `core-developer-prompt.md` | Системный промпт — начать здесь |
| `Каркас/prompt-каркас.md` | Внутреннее устройство core |
| `../packages/core/tests/` | Тесты как документация |

## Технологический стек

| Компонент | Технология |
|---|---|
| Язык | Python 3.12+ |
| CLI-фреймворк | Typer |
| ORM | SQLAlchemy 2.0 (синхронный) |
| Модели | Pydantic v2 |
| Миграции | Alembic |
| Логирование | loguru |
| Шифрование | cryptography (Fernet) |
| Сборка | hatchling |
| Тестирование | pytest, CliRunner |
| Веб-интерфейс | FastAPI + React 18 + Tailwind CSS 4 |

## Архитектура

```
ai-mini-box-core ─── единственный обязательный пакет
       │
       ├── ai-mini-box-web       (PWA-интерфейс, REST API)
       ├── ai-mini-box-telegram  (Telegram-бот)
       ├── ai-mini-box-llm       (LLM — в разработке)
       ├── ai-mini-box-demo      (демо-пример)
       └── ai-mini-box-{твой}    ← твой плагин
```

Плагины общаются через Service Registry (`core/services/registry.py`), а не прямыми импортами.

## Быстрые команды

```bash
pip install -e packages/core/              # установить core в dev-режиме
pytest packages/core/tests/ -v             # запустить тесты core
python -m ai_mini_box init                 # инициализировать проект
python -m ai_mini_box db upgrade           # накатить миграции
python -m ai_mini_box config show          # показать конфиг
python -m ai_mini_box --help               # список команд
```