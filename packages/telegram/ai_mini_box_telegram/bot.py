import requests

from .exceptions import TelegramAPIError


class TelegramBot:
    BASE = "https://api.telegram.org/bot"

    def __init__(self, token: str):
        self.token = token

    def _url(self, method: str) -> str:
        return f"{self.BASE}{self.token}/{method}"

    def get_updates(self, offset: int | None = None, timeout: int = 10) -> list[dict]:
        url = self._url("getUpdates")
        params: dict = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset
        try:
            resp = requests.get(url, params=params, timeout=timeout + 5)
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
            resp = requests.get(url, timeout=10)
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
            resp = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
            return resp.ok
        except requests.exceptions.RequestException:
            return False
