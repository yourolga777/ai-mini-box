# Шаблон плагина ai-mini-box — краткая памятка

Для полной версии с кодом — см. соответствующий файл из `plugins/`.

## Структура

```
ai-mini-box-{name}/
├── pyproject.toml
├── ai_mini_box_{name}/
│   ├── __init__.py
│   ├── commands.py          # register(app) + CLI команды
│   ├── core.py              # бизнес-логика (опционально)
│   ├── config_provider.py   # ConfigProvider для веб-интерфейса (опционально)
│   └── help/                # help-секции для web UI (опционально)
└── tests/
    ├── test_commands.py
    └── test_core.py
```

## pyproject.toml — главное

- Сборка: `hatchling`
- Имя: `ai-mini-box-{name}`
- Зависимость: `"ai-mini-box-core>=5.0.0"`
- Entry point: `[project.entry-points."ai_mini_box.tools"]` → `{name} = "...commands:register"`
- ConfigProvider (если нужен веб-доступ): `[project.entry-points."ai_mini_box.config_provider"]` → `{name} = "...config_provider:config_provider"`

Подробнее: `01-package-setup.md`

## CLI-команды

```python
def register(app: typer.Typer):
    grp = typer.Typer(help="...")
    app.add_typer(grp, name="{name}")

    @grp.command()
    def my_cmd(): ...
```

Подробнее: `02-cli-entry-point.md`

## БД

```python
with get_db() as session:
    repos = RepoContainer(session)
    items = repos.contacts.list()
```

Mock-репозитории: `from ai_mini_box.testing import MockContactRepo`

Подробнее: `03-database.md`, `06-testing.md`

## Демон (фоновый процесс)

- Команда `daemon` — web UI автоматом показывает кнопки Start/Stop
- Обрабатывать SIGTERM/SIGINT
- Перезагружать конфиг каждый цикл

Подробнее: `02-cli-entry-point.md`, `09-web-management.md`

## Сервис для других плагинов (опционально)

```python
from ai_mini_box.core.services.registry import register_service
register_service("{name}", MyServiceImpl())
```

Подробнее: `10-service-registry.md`

## ConfigProvider

Если плагин имеет настройки, которые должны быть видны/редактируемы через веб-интерфейс:

1. Реализуй `ConfigProvider` (три метода: `get_config`, `set_config`, `get_schema`)
2. Зарегистрируй entry point `ai_mini_box.config_provider`

Подробнее: `docs/plugins/12-config-provider.md`, `docs/specs/28-config-provider-core.md`.

## Чек-лист перед публикацией

- [ ] Имя: `ai-mini-box-{name}`
- [ ] Entry point `ai_mini_box.tools` зарегистрирован
- [ ] ConfigProvider зарегистрирован (если плагин имеет настройки для веба)
- [ ] `"ai-mini-box-core>=5.0.0"` в зависимостях
- [ ] Тесты проходят: `pytest tests/ -v`
- [ ] README с установкой и примерами
- [ ] Логи в отдельный файл `logs/plugin_{name}.log`
- [ ] Нет импортов других плагинов (только core)
- [ ] Версия в pyproject.toml соответствует семверу

Подробнее: `07-publishing.md`