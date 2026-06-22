# Changelog

## [5.0.0] — 2026-06-22

Первый публичный релиз. Системное ядро для автоматизации малого бизнеса.

### Added

- **Pydantic-модели** — Contact, Product, Message, Order с типизированными полями и Enum
- **Repository ABC** — ContactRepo, ProductRepo, MessageRepo, OrderRepo с QueryBuilder (filter, search, sort, limit, offset)
- **SQLAlchemy implementation** — ORM-модели (ContactModel, ProductModel, MessageModel, OrderModel) и готовые репозитории
- **RepoContainer** — DI-контейнер с фабрикой: `RepoContainer(session).contacts` / `.products` / `.messages` / `.orders`
- **AppContext** — синглтон-контекст приложения с конфигурацией и репозиториями
- **CLI на Typer** — `init`, `check-db`, `config show/set/unset`, `--verbose`
- **Плагинная система** — сервисы подключаются через `[project.entry-points."ai_mini_box.tools"]`
- **JsonConfigManager** — чтение/запись `config.json` с шифрованием чувствительных полей (Fernet + PBKDF2HMAC)
- **Loguru-логгер** — `setup_logging(verbose)`
- **Alembic-совместимость** — `Base.metadata` для миграций
- **Демо-сервис** — пакет `ai-mini-box-demo` с 3 командами и 9 тестами
- **CI/CD** — GitHub Actions: тесты (3.12, 3.13) + публикация в PyPI по тегу
- **Документация** — README, developer-guide, CHANGELOG
- **Тесты** — 72 теста (63 core + 9 demo), покрытие ключевых сценариев

### Changed

- Абстракции `core/` отделены от реализации `infrastructure/`
- CLI переведён с прямых вызовов на плагинную загрузку через entry points

### Fixed

- `hasattr()` для Pydantic v2 заменён на `key in AppConfig.model_fields`
- `PBKDF2HMAC` вызов исправлен на `.derive()` с base64-кодированием
- `load()` теперь дешифрует чувствительные поля
- Поиск по кириллице — Python-side `.lower()` вместо SQLite `LOWER()`
