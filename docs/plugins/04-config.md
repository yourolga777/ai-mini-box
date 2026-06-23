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

## Available config fields

| Field | Type | Default | Description |
|---|---|---|---|
| `telegram_token` | `str` | `""` | Telegram bot token |
| `telegram_allowed_chat_ids` | `list[int]` | `[]` | Allowed chat IDs |
| `email_imap_server` | `str` | `""` | IMAP server |
| `email_login` | `str` | `""` | Email login |
| `email_password` | `str` | `""` | Email password (encrypted) |
| `poll_interval` | `int` | `30` | Poll interval in seconds |

Sensitive fields (password, token) are automatically encrypted with Fernet when saved.

## Setting config from CLI

```bash
ai-mini-box config set telegram_token "your_token_here"
ai-mini-box config set poll_interval 15
```

## Adding custom config (for advanced use)

If your plugin needs custom config fields, you can extend the config model (requires modifying core). For simple cases, use environment variables or a separate config file.
