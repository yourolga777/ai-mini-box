import json
import os
from pathlib import Path


class TelegramPluginConfig:
    def __init__(self, path: str = "data/telegram_config.json"):
        self._path = Path(path)
        self._data = self._load()

    @staticmethod
    def _defaults() -> dict:
        return {
            "api_base_url": "https://api.telegram.org/bot",
            "request_timeout": 10,
            "poll_interval": 2,
        }

    def _load(self) -> dict:
        if not self._path.exists():
            self._path.parent.mkdir(parents=True, exist_ok=True)
            data = self._defaults()
            self._write(data)
            return data
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception):
            return self._defaults()

    def _write(self, data: dict) -> None:
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(tmp, self._path)

    @property
    def api_base_url(self) -> str:
        return self._data.get("api_base_url", self._defaults()["api_base_url"])

    @property
    def request_timeout(self) -> int:
        return self._data.get("request_timeout", self._defaults()["request_timeout"])

    @property
    def poll_interval(self) -> int:
        return self._data.get("poll_interval", self._defaults()["poll_interval"])

    def set(self, key: str, value) -> None:
        self._data[key] = value
        self._write(self._data)

    def all(self) -> dict:
        return dict(self._data)