import requests
from loguru import logger

from ai_mini_box.infrastructure.config import JsonConfigManager
from ai_mini_box.infrastructure.database import get_db

from .config import TelegramPluginConfig
from .exceptions import TelegramAPIError
from .handlers import process_update
from .state import FileTelegramStateRepo


class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        cfg = TelegramPluginConfig()
        self.base_url = cfg.api_base_url
        self.timeout = cfg.request_timeout

    def _url(self, method: str) -> str:
        return f"{self.base_url}{self.token}/{method}"

    def get_updates(self, offset: int | None = None, timeout: int | None = None) -> list[dict]:
        actual_timeout = timeout or self.timeout
        url = self._url("getUpdates")
        params: dict = {"timeout": actual_timeout}
        if offset is not None:
            params["offset"] = offset
        try:
            resp = requests.get(url, params=params, timeout=actual_timeout + 5)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as e:
            raise TelegramAPIError(str(e), status_code=getattr(e.response, "status_code", 0)) from e
        if not data.get("ok"):
            raise TelegramAPIError(data.get("description", "Unknown error"), status_code=0)
        return data["result"]

    def get_me(self) -> dict:
        url = self._url("getMe")
        try:
            resp = requests.get(url, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as e:
            raise TelegramAPIError(str(e), status_code=getattr(e.response, "status_code", 0)) from e
        if not data.get("ok"):
            raise TelegramAPIError(data.get("description", "Unknown error"), status_code=0)
        return data["result"]

    def send_message(self, chat_id: int, text: str) -> bool:
        url = self._url("sendMessage")
        try:
            resp = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=self.timeout)
            if not resp.ok:
                logger.error("Telegram send_message failed: HTTP {}", resp.status_code)
            return resp.ok
        except requests.exceptions.RequestException as e:
            logger.error("Telegram send_message network error: {}", e)
            return False


class TelegramService:
    """Public API for other plugins (registered in Service Registry)."""

    def send_message(self, chat_id: int, text: str) -> bool:
        config = JsonConfigManager().load()
        if not config.telegram_token:
            logger.error("TelegramService.send_message: token not set")
            return False
        bot = TelegramBot(config.telegram_token)
        return bot.send_message(chat_id, text)

    def verify_token(self) -> dict:
        config = JsonConfigManager().load()
        bot = TelegramBot(config.telegram_token)
        return bot.get_me()

    def poll(self, allowed_chat_ids: list[int] | None = None) -> dict:
        """
        Poll Telegram for new messages once.

        Args:
            allowed_chat_ids: Override for chat whitelist.
                              If None, reads from AppConfig.

        Returns:
            dict with keys:
                success (bool)
                count (int)
                detected_chat_ids (list[int])
                error (str | None)
        """
        config = JsonConfigManager().load()
        token = config.telegram_token
        if not token:
            return {"success": False, "count": 0, "detected_chat_ids": [], "error": "telegram_token not set"}

        if allowed_chat_ids is None:
            allowed_chat_ids = config.telegram_allowed_chat_ids

        bot = TelegramBot(token)
        state = FileTelegramStateRepo()
        offset = state.get_offset()

        try:
            updates = bot.get_updates(offset=offset)
        except TelegramAPIError as e:
            return {"success": False, "count": 0, "detected_chat_ids": [], "error": str(e)}
        except Exception as e:
            logger.error("TelegramService.poll: unexpected error: {}", e)
            return {"success": False, "count": 0, "detected_chat_ids": [], "error": f"Unexpected error: {e}"}

        count = 0
        detected_chat_ids: list[int] = []
        for update in updates:
            with get_db() as session:
                if process_update(update, session, allowed_chat_ids=allowed_chat_ids):
                    count += 1
            state.save_offset(update["update_id"] + 1)
            msg_data = update.get("message") or update.get("business_message")
            if msg_data:
                cid = msg_data["chat"]["id"]
                if cid not in detected_chat_ids:
                    detected_chat_ids.append(cid)

        return {
            "success": True,
            "count": count,
            "detected_chat_ids": detected_chat_ids,
            "error": None,
        }
