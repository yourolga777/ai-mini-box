# Telegram Plugin Guide

Telegram-specific patterns and pitfalls discovered while building the official Telegram plugin.

## Setup flow

Recommended sequence for setting up a Telegram plugin via the web UI:

1. **Save token** → enter bot token from BotFather
2. **Verify token** → calls `getMe` to confirm token is valid; saves bot name and username
3. **Poll once** → fetches pending updates; detects chat IDs from incoming messages
4. **Whitelist** → add detected chat IDs to `allowed_chat_ids` (or leave `[]` to accept all)
5. **Start daemon** → continuous polling loop
6. **Test** → send a message to the bot from another account → verify it appears in /messages

## Offset tracking: advance for EVERY update

The Telegram API returns an `update_id` for every item in the response — including non-message updates like `business_connection`, `my_chat_member`, etc.

**Critical:** advance your offset for **every** update, not just successfully processed ones. Updates you skip or ignore will otherwise be re-delivered forever.

```python
# WRONG — non-message updates get stuck
for update in updates:
    if process(update):
        state.save_offset(update["update_id"] + 1)

# RIGHT — offset advances regardless
for update in updates:
    count += process(update)
    state.save_offset(update["update_id"] + 1)
```

The Telegram plugin uses `FileTelegramStateRepo` (JSON file in `data/`) for offset persistence between daemon restarts.

## Business API

Telegram Business API sends business messages as `business_message` instead of `message`. Handle both:

```python
def process_update(update: dict) -> bool:
    event = (
        update.get("message")
        or update.get("business_message")
        or update.get("channel_post")
    )
    if event is None:
        return False  # skip unknown type (offset still advances)
    # ... process event
```

### Business connection

When a business account is linked, Telegram sends a `business_connection` update:

```json
{
    "update_id": 123,
    "business_connection": {
        "id": "conn_abc123",
        "user_id": 8412879460,
        "user": {"id": 8412879460, ...},
        "is_enabled": true,
        "can_reply": false
    }
}
```

This update appears **once** when the connection is established. It must be skipped (return `False`) but the offset must still advance — otherwise it repeats forever.

### Secretary Mode

If `can_reply` is `false`, the bot cannot reply to business messages directly. To enable replies:

1. Open [@BotFather](https://t.me/botfather)
2. `/mybots` → select your bot → **Bot Settings** → **Secretary Mode** → **Turn on**

Without Secretary Mode enabled, `send_message` to a business chat will fail silently or return error.

## Config: reload each cycle

The daemon must reload config inside the polling loop, not once at startup:

```python
while not stop:
    config = JsonConfigManager().load()  # fresh each cycle
    token = config.telegram_token        # may have changed via web UI
    allowed = config.telegram_allowed_chat_ids
    # ... poll Telegram API ...
    time.sleep(config.poll_interval)
```

Config changes (token, allowed IDs, interval) made via the web UI only take effect on the next cycle.

## Two config APIs warning

- `JsonConfigManager().load()` → returns `AppConfig` with the **decrypted** token. Use in daemon and API handlers.
- `_manager.get_config()` (in `PluginManager`) → returns a dict with masked token (`"***"`). Used by web UI config endpoint.

**Do NOT use `_manager.get_config()` in your daemon** — the token will be `"***"` and all API calls to Telegram will fail.

## Extracted fields

When processing a message, the Telegram plugin enriches the `Message` model:

| Field | Source | Description |
|---|---|---|
| `extracted_phone` | `core.extraction.extract_phone()` | Regex-extracted phone number (7-15 digits with optional + and formatting) |
| `extracted_name` | `event["from"].first_name + last_name` | Sender's display name from Telegram metadata |
| `draft_response` | `core.answer_service.auto_draft_response()` | Auto-generated reply from Knowledge Base (LLM fallback is a placeholder) |

## State persistence

Use `FileTelegramStateRepo` to persist offset between daemon restarts:

```python
class FileTelegramStateRepo:
    def __init__(self, path: str = "data/telegram_state.json"):
        self._path = Path(path)

    def get_offset(self) -> int | None:
        if not self._path.exists():
            return None
        data = json.loads(self._path.read_text(encoding="utf-8"))
        return data.get("offset")

    def save_offset(self, offset: int) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps({"offset": offset}), encoding="utf-8")
```

## Known pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| Offset not advanced for non-message updates | `business_connection` repeats on every poll | Advance offset for **every** update, not just processed ones |
| Config loaded once at daemon start | Token changes via web UI are ignored | Reload `JsonConfigManager().load()` each cycle |
| Token read via `_manager.get_config()` | Token is `"***"`, API calls fail | Use `JsonConfigManager().load()` instead |
| `can_reply=false` | Replies to business messages fail silently | Enable Secretary Mode in @BotFather |
| `Base.metadata.create_all()` runs before migration | Migration fails with "table already exists" | Guard `create_table` with `inspector.get_table_names()` |
