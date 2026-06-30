# Spec 31 — TelegramConfigProvider (telegram-dev)

## Goal

Реализовать `ConfigProvider` для Telegram-плагина, чтобы веб-интерфейс мог читать и изменять конфиг Telegram-бота через единый протокол.

## Зависимость

**Блокер:** Spec 28 (core-dev) — должен быть определён `ConfigProvider` protocol.

## Что сделать

### 1. Создать файл `ai_mini_box_telegram/config_provider.py`

```python
"""ConfigProvider для Telegram-плагина.

Telegram-плагин хранит конфиг в data/config.json через JsonConfigManager
(поля: telegram_token, telegram_bot_name, telegram_bot_username,
telegram_allowed_chat_ids, poll_interval).

Этот провайдер читает/пишет через JsonConfigManager, а не напрямую в JSON.
"""

from __future__ import annotations


class TelegramConfigProvider:
    """ConfigProvider для Telegram-плагина.

    Читает/пишет конфиг через JsonConfigManager (data/config.json).
    Чувствительные поля (telegram_token) маскирует.
    """

    def get_config(self) -> dict:
        from ai_mini_box.infrastructure.config import JsonConfigManager
        config = JsonConfigManager().load()
        return {
            "telegram_token": "***" if config.telegram_token else "",
            "telegram_bot_name": config.telegram_bot_name or "",
            "telegram_bot_username": config.telegram_bot_username or "",
            "telegram_allowed_chat_ids": list(config.telegram_allowed_chat_ids or []),
            "poll_interval": config.poll_interval or 30,
        }

    def set_config(self, config: dict) -> dict:
        manager = JsonConfigManager()
        try:
            for key in ("telegram_bot_name", "telegram_bot_username",
                        "telegram_allowed_chat_ids", "poll_interval"):
                if key in config:
                    manager.set(key, config[key])
            # token — отдельно, т.к. шифруется
            token = config.get("telegram_token", "")
            if token and token != "***":
                manager.set("telegram_token", token)
            return {"success": True}
        except (ValueError, Exception) as e:
            return {"success": False, "error": str(e)}

    def get_schema(self) -> dict:
        return {
            "$schema": "https://json-schemas.org/draft/2020-12/schema",
            "type": "object",
            "title": "Telegram Bot Config",
            "properties": {
                "telegram_token": {
                    "type": "string",
                    "title": "Bot Token",
                    "description": "Токен бота (получается у @BotFather)",
                    "secret": True,
                },
                "telegram_bot_name": {
                    "type": "string",
                    "title": "Имя бота",
                    "description": "Отображаемое имя бота",
                },
                "telegram_bot_username": {
                    "type": "string",
                    "title": "@username",
                    "description": "Username бота (без @)",
                },
                "telegram_allowed_chat_ids": {
                    "type": "array",
                    "title": "Разрешённые чаты",
                    "description": "ID чатов, которым разрешён доступ",
                    "items": {"type": "integer"},
                },
                "poll_interval": {
                    "type": "integer",
                    "title": "Интервал опроса (сек)",
                    "default": 30,
                    "minimum": 5,
                    "maximum": 300,
                },
            },
            "required": ["telegram_token"],
        }


# Экспорт для entry point
config_provider = TelegramConfigProvider()
```

### 2. Зарегистрировать entry point в `pyproject.toml`

```toml
[project.entry-points."ai_mini_box.config_provider"]
telegram = "ai_mini_box_telegram.config_provider:config_provider"
```

### 3. Если `pyproject.toml` не существует — проверить

Убедиться, что Telegram-плагин использует hatchling и в `pyproject.toml` есть секция `[project.entry-points]`.

## Маскировка токена

`telegram_token` — чувствительное поле. В `get_config()` оно возвращается как `"***"` (как и в `PluginManager.get_config()`). При `set_config()` — если значение `"***"`, оно не перезаписывает существующий токен. Если пришло новое значение — сохраняется с шифрованием через `JsonConfigManager.set()`.

## Эффект

После деплоя spec 29 (web-dev) + spec 31:
- `GET /api/plugins/telegram/config` → JSON с полями Telegram-конфига (токен маскирован)
- `POST /api/plugins/telegram/config` → сохраняет через `JsonConfigManager`
- `GET /api/plugins/telegram/config-schema` → JSON Schema с полем token типа `secret`

## Acceptance Criteria

- [ ] `TelegramConfigProvider.get_config()` возвращает `telegram_token: "***"` (не пустую строку, если токен есть)
- [ ] `TelegramConfigProvider.set_config({"telegram_token": "new_token"})` сохраняет токен через `JsonConfigManager`
- [ ] `TelegramConfigProvider.set_config({"telegram_token": "***"})` НЕ перезаписывает существующий токен
- [ ] `TelegramConfigProvider.set_config({"poll_interval": 60})` обновляет только poll_interval
- [ ] `TelegramConfigProvider.get_schema()` возвращает JSON Schema с полем `telegram_token` типа `secret`
- [ ] Entry point `ai_mini_box.config_provider` зарегистрирован
- [ ] При отсутствии `data/config.json` `get_config()` возвращает значения по умолчанию (не падает)
