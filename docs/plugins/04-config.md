# Configuration

Use `JsonConfigManager` to read configuration values set by the user.

## Reading config

```python
from ai_mini_box.infrastructure.config import JsonConfigManager

config = JsonConfigManager().load()

# Read typed fields
token = config.telegram_token       # str
interval = config.poll_interval     # int
allowed_ids = config.telegram_allowed_chat_ids  # list[int]
```

Sensitive fields (`telegram_token`, `email_password`, `whatsapp_api_key`, etc.) are automatically encrypted with Fernet (PBKDF2HMAC) when saved and decrypted on load. The encryption key is derived from `AI_BOX_SECRET` env var (or `"default-dev-secret"` fallback).

### ⚠️ Two config APIs — use the right one

- `JsonConfigManager().load()` → returns `AppConfig` with decrypted sensitive fields. Use this in daemons and API handlers.
- `_manager.get_config()` (in `PluginManager`) → returns a dict with masked sensitive values (`"***"`). This is used by the web UI config endpoint to avoid leaking secrets to the frontend.

**Do NOT use `_manager.get_config()` for your daemon** — the token will be `"***"` and API calls will fail.

### Config changes require daemon restart

Changing config via the web UI or CLI modifies the JSON file, but the running daemon has already loaded the old values into memory. You must **Stop** and **Start** the daemon for changes to apply.

## Environment variable overrides

Any config field can be overridden via `AI_BOX_<FIELD_NAME>` env var:

```bash
set AI_BOX_TELEGRAM_TOKEN=my_token
set AI_BOX_POLL_INTERVAL=15
```

Env vars take priority over JSON file values. Useful for secrets in production and for tests.

## Available config fields

Config is grouped into sections. All fields are defined in the `AppConfig` Pydantic model.

### Telegram

| Field | Type | Default | Description |
|---|---|---|---|
| `telegram_token` | `str` | `""` | Bot token (encrypted) |
| `telegram_bot_name` | `str` | `""` | Bot display name |
| `telegram_bot_username` | `str` | `""` | Bot @username |
| `telegram_allowed_chat_ids` | `list[int]` | `[]` | Allowed chat/group IDs |

### Email

| Field | Type | Default | Description |
|---|---|---|---|
| `email_imap_server` | `str` | `imap.yandex.ru` | IMAP server host |
| `email_imap_port` | `int` | `993` | IMAP server port |
| `email_login` | `str` | `""` | Email login |
| `email_password` | `str` | `""` | Email password (encrypted) |

### LLM

| Field | Type | Default | Description |
|---|---|---|---|
| `llm_model_path` | `str` | `models/Phi-3-mini-q4.gguf` | Path to GGUF model |
| `llm_n_ctx` | `int` | `4096` | Context window size |
| `llm_n_threads` | `int` | `4` | CPU threads for inference |

### WhatsApp

| Field | Type | Default | Description |
|---|---|---|---|
| `whatsapp_api_key` | `str` | `""` | API key (encrypted) |
| `whatsapp_phone` | `str` | `""` | Business phone number |

### SMS

| Field | Type | Default | Description |
|---|---|---|---|
| `sms_provider` | `str` | `""` | SMS provider name |
| `sms_api_key` | `str` | `""` | SMS API key (encrypted) |
| `sms_api_secret` | `str` | `""` | SMS API secret (encrypted) |

### Payments: YooKassa

| Field | Type | Default | Description |
|---|---|---|---|
| `yookassa_shop_id` | `str` | `""` | Shop ID |
| `yookassa_secret_key` | `str` | `""` | Secret key (encrypted) |

### Payments: Tinkoff

| Field | Type | Default | Description |
|---|---|---|---|
| `tinkoff_terminal_key` | `str` | `""` | Terminal key |
| `tinkoff_password` | `str` | `""` | Password (encrypted) |

### Payments: Sber

| Field | Type | Default | Description |
|---|---|---|---|
| `sber_merchant_id` | `str` | `""` | Merchant ID |
| `sber_login` | `str` | `""` | Login |
| `sber_password` | `str` | `""` | Password (encrypted) |

### Schedule

| Field | Type | Default | Description |
|---|---|---|---|
| `work_schedule_start` | `str` | `09:00` | Work day start (HH:MM) |
| `work_schedule_end` | `str` | `18:00` | Work day end (HH:MM) |

### Notifications

| Field | Type | Default | Description |
|---|---|---|---|
| `notification_on_order` | `bool` | `True` | Notify on new order |
| `notification_on_complaint` | `bool` | `True` | Notify on complaint |
| `notification_on_error` | `bool` | `True` | Notify on system error |

### General

| Field | Type | Default | Description |
|---|---|---|---|
| `poll_interval` | `int` | `30` | Daemon poll interval (seconds) |
| `auto_backup_interval` | `int` | `0` | Auto-backup interval (hours, 0 = disabled) |

## Setting config from CLI

```bash
ai-mini-box config set telegram_token "your_token_here"
ai-mini-box config set poll_interval 15
ai-mini-box config set telegram_allowed_chat_ids "[123,456]"
```

Type coercion is automatic: `"15"` → `int`, `"true"` → `bool`, `"[1,2,3]"` → `list[int]`.

## Config Provider Protocol (рекомендовано)

**С версии core 5.1.0** появился единый протокол expose конфига плагина в веб-интерфейс. Если твой плагин имеет настройки, которые пользователь должен видеть/менять через веб — реализуй `ConfigProvider`.

### Как это работает

1. Core определяет протокол `ConfigProvider` (см. `ai_mini_box.core.services.config_provider`)
2. Плагин реализует класс с тремя методами: `get_config()`, `set_config()`, `get_schema()`
3. Плагин регистрирует экземпляр через entry point `ai_mini_box.config_provider` в `pyproject.toml`
4. Web-интерфейс находит провайдера и использует его для чтения/записи конфига

### Пример реализации

**`ai_mini_box_myplugin/config_provider.py`:**

```python
from __future__ import annotations

class MyPluginConfigProvider:
    def get_config(self) -> dict:
        from .config import MyConfig
        cfg = MyConfig.load()
        return {
            "api_key": "***" if cfg.api_key else "",
            "poll_interval": cfg.poll_interval,
            "enabled": cfg.enabled,
        }

    def set_config(self, config: dict) -> dict:
        from .config import MyConfig
        cfg = MyConfig.load()
        if "poll_interval" in config:
            cfg.poll_interval = int(config["poll_interval"])
        if "enabled" in config:
            cfg.enabled = bool(config["enabled"])
        api_key = config.get("api_key", "")
        if api_key and api_key != "***":
            cfg.api_key = api_key
        cfg.save()
        return {"success": True}

    def get_schema(self) -> dict:
        return {
            "$schema": "https://json-schemas.org/draft/2020-12/schema",
            "type": "object",
            "title": "My Plugin Config",
            "properties": {
                "api_key": {
                    "type": "string",
                    "title": "API Key",
                    "secret": True,
                },
                "poll_interval": {
                    "type": "integer",
                    "title": "Poll interval (sec)",
                    "default": 30,
                },
                "enabled": {
                    "type": "boolean",
                    "title": "Enabled",
                    "default": True,
                },
            },
            "required": [],
        }

config_provider = MyPluginConfigProvider()
```

**`pyproject.toml`:**

```toml
[project.entry-points."ai_mini_box.config_provider"]
myplugin = "ai_mini_box_myplugin.config_provider:config_provider"
```

### Entry point groups — сводка

| Группа | Назначение | Обязательность |
|--------|-----------|:---:|
| `ai_mini_box.tools` | CLI-команды (`register(app)`) | **Да** |
| `ai_mini_box.config_provider` | ConfigProvider для веб-интерфейса | Рекомендовано |
| `ai_mini_box.help` | help-секции для веб-интерфейса | Опционально |

### Правила для ConfigProvider

1. **Маскируй секреты.** В `get_config()` возвращай `"***"` для токенов/паролей. В `set_config()` — если пришло `"***"`, не перезаписывай существующее значение.
2. **Merge, не replace.** `set_config()` получает только те поля, которые пользователь изменил. Не затирай остальные.
3. **Не меняй формат своего конфига.** Если плагин уже использует свой JSON-файл — продолжай его использовать. ConfigProvider — это прослойка для веба, не замена.
4. **JSON Schema для формы.** `get_schema()` возвращает схему в формате JSON Schema draft 2020-12. Поле с `"secret": True` будет показано как поле для ввода пароля (с кнопкой "показать/скрыть").

### Что если не зарегистрировать ConfigProvider?

Веб-интерфейс пытается открыть страницу настроек плагина → `GET /api/plugins/{name}/config`:
1. Ищет ConfigProvider — не находит
2. Fallback: читает `data/config.json["{name}"]`
3. Если и там нет — **404**

**Без ConfigProvider настройки плагина будут недоступны в веб-интерфейсе.**

Подробнее: `docs/plugins/12-config-provider.md`, спецификации `docs/specs/28-31-*`.

## Альтернативы (не рекомендованы для новых плагинов)

Если плагин совсем простой (2-3 поля) — можно использовать эти подходы, но для веб-доступа всё равно потребуется ConfigProvider.

### Option A — Отдельный JSON-файл

```python
import json
from pathlib import Path

class MyPluginConfig:
    def __init__(self, path: str = "data/my_plugin_config.json"):
        self.path = Path(path)

    def load(self) -> dict:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, data: dict):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
```

### Option B — Environment variables

```bash
set MY_PLUGIN_API_KEY=abc123
```

```python
import os
api_key = os.environ.get("MY_PLUGIN_API_KEY", "")
```
