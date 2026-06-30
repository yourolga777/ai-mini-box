from __future__ import annotations


class TelegramConfigProvider:
    """ConfigProvider for Telegram plugin.

    Reads/writes config through JsonConfigManager (data/config.json).
    Sensitive fields (telegram_token) are masked.
    """

    def __init__(self, config_path: str | None = None):
        self._config_path = config_path

    def _get_manager(self):
        from ai_mini_box.infrastructure.config import JsonConfigManager
        if self._config_path:
            return JsonConfigManager(self._config_path)
        return JsonConfigManager()

    def get_config(self) -> dict:
        config = self._get_manager().load()
        return {
            "telegram_token": "***" if config.telegram_token else "",
            "telegram_bot_name": config.telegram_bot_name or "",
            "telegram_bot_username": config.telegram_bot_username or "",
            "telegram_allowed_chat_ids": list(config.telegram_allowed_chat_ids or []),
            "poll_interval": config.poll_interval or 30,
        }

    def set_config(self, config: dict) -> dict:
        manager = self._get_manager()
        try:
            for key in ("telegram_bot_name", "telegram_bot_username",
                        "telegram_allowed_chat_ids", "poll_interval"):
                if key in config:
                    manager.set(key, config[key])
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
                    "description": "Token for the bot (get from @BotFather)",
                    "secret": True,
                },
                "telegram_bot_name": {
                    "type": "string",
                    "title": "Bot Name",
                    "description": "Display name of the bot",
                },
                "telegram_bot_username": {
                    "type": "string",
                    "title": "@username",
                    "description": "Bot username (without @)",
                },
                "telegram_allowed_chat_ids": {
                    "type": "array",
                    "title": "Allowed chats",
                    "description": "Chat IDs that are allowed access",
                    "items": {"type": "integer"},
                },
                "poll_interval": {
                    "type": "integer",
                    "title": "Poll interval (sec)",
                    "default": 30,
                    "minimum": 5,
                    "maximum": 300,
                },
            },
            "required": ["telegram_token"],
        }


config_provider = TelegramConfigProvider()
