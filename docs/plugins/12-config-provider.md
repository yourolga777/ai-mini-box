# Config Provider Protocol

## Overview

`ConfigProvider` — единый протокол для expose конфига плагина в веб-интерфейс. Введён в core 5.1.0 (spec 28).

```
web-ui → GET /api/plugins/{name}/config
              → PluginManager.get_plugin_config(name)
                    → get_config_provider(name)?.get_config()
                          ?? fallback data/config.json[name]
```

## Protocol definition

Расположение: `ai_mini_box/core/services/config_provider.py`

```python
from typing import Protocol, runtime_checkable


@runtime_checkable
class ConfigProvider(Protocol):
    def get_config(self) -> dict: ...
    def set_config(self, config: dict) -> dict: ...
    def get_schema(self) -> dict: ...
```

### Methods

| Method | Возврат | Описание |
|--------|---------|----------|
| `get_config()` | `dict` | Текущий конфиг плагина. Чувствительные поля маскированы (`"***"`). |
| `set_config(config)` | `dict` | Сохранить конфиг (merge). Возвращает `{"success": True}` или `{"success": False, "error": "..."}`. |
| `get_schema()` | `dict` | JSON Schema draft 2020-12 для построения формы. |

## Entry point

Плагин регистрирует экземпляр `ConfigProvider` в `pyproject.toml`:

```toml
[project.entry-points."ai_mini_box.config_provider"]
llm = "ai_mini_box_llm.plugin:config_provider"
```

где `config_provider` — глобальный экземпляр класса, реализующего протокол.

## Discovery

Core предоставляет функции поиска:

```python
from ai_mini_box.core.services.config_provider import get_config_provider, discover_config_providers

# По имени плагина
provider = get_config_provider("llm")
if provider:
    cfg = provider.get_config()

# Все провайдеры
all_providers = discover_config_providers()  # {"llm": <obj>, "telegram": <obj>}
```

## Правила реализации

### 1. Маскировка секретов

В `get_config()` токены/пароли возвращаются как `"***"`:

```python
def get_config(self) -> dict:
    return {
        "api_key": "***" if self._real_key else "",
        "poll_interval": 30,
    }
```

В `set_config()` — если значение `"***"`, оно **не перезаписывает** существующее:

```python
def set_config(self, config: dict) -> dict:
    api_key = config.get("api_key", "")
    if api_key and api_key != "***":
        self._save_api_key(api_key)
    return {"success": True}
```

### 2. Merge-семантика

`set_config()` получает **только изменённые** поля. Не обнуляй то, что не пришло:

```python
# Правильно — обновляем только переданное
if "poll_interval" in config:
    cfg.poll_interval = int(config["poll_interval"])

# Неправильно — заменяет весь конфиг
cfg = Config(**config)  # так нельзя
```

### 3. Схема с secret-полями

В JSON Schema укажи `"secret": True` для полей с паролями/токенами. Веб-интерфейс покажет их как `<input type="password">`:

```python
def get_schema(self) -> dict:
    return {
        "type": "object",
        "properties": {
            "api_key": {
                "type": "string",
                "title": "API Key",
                "secret": True,  # <- маскированный ввод
            },
        },
    }
```

### 4. Изоляция хранилища

ConfigProvider — прослойка между вебом и твоим конфиг-файлом. Не меняй формат хранения. Если плагин использует `data/myplugin_config.json` — продолжай его использовать. `get_config()` читает оттуда, `set_config()` пишет туда.

### 5. Обработка ошибок

Если `set_config()` не может сохранить — верни `{"success": False, "error": "причина"}`. Не бросай исключения.

Если `get_config()` не может загрузить — верни `{}` (пустой конфиг), не падай.

## Testing

```python
def test_config_provider():
    provider = MyPluginConfigProvider()

    # get_config
    cfg = provider.get_config()
    assert isinstance(cfg, dict)
    assert "api_key" in cfg

    # set_config (merge)
    result = provider.set_config({"poll_interval": 60})
    assert result["success"] is True
    assert provider.get_config()["poll_interval"] == 60

    # schema
    schema = provider.get_schema()
    assert "properties" in schema
    assert "type" in schema

    # mask handling
    result = provider.set_config({"api_key": "***"})
    assert result["success"] is True  # не перезаписал
```

## Migration guide (для существующих плагинов)

Если у плагина **уже есть** свой конфиг (через `JsonConfigManager` или отдельный JSON-файл):

1. Создай `config_provider.py` с классом, реализующим протокол
2. В `get_config()` читай из существующего хранилища
3. В `set_config()` пиши в существующее хранилище
4. Добавь entry point в `pyproject.toml`
5. Протестируй через веб-интерфейс

## Related specs

| Spec | Роль | Описание |
|------|------|----------|
| 28 | core-dev | Protocol definition + discovery |
| 29 | web-dev | PluginManager integration |
| 30 | llm-dev | LlmConfigProvider |
| 31 | telegram-dev | TelegramConfigProvider |
