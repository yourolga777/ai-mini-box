import json
import os
from abc import ABC, abstractmethod
from pathlib import Path


class TelegramStateRepo(ABC):
    @abstractmethod
    def get_offset(self) -> int | None:
        ...

    @abstractmethod
    def save_offset(self, offset: int) -> None:
        ...


class MemoryTelegramStateRepo(TelegramStateRepo):
    def __init__(self):
        self._offset: int | None = None

    def get_offset(self) -> int | None:
        return self._offset

    def save_offset(self, offset: int) -> None:
        self._offset = offset


class FileTelegramStateRepo(TelegramStateRepo):
    def __init__(self, path: str = "data/telegram_state.json"):
        self._path = Path(path)

    def get_offset(self) -> int | None:
        if not self._path.exists():
            return None
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            value = data.get("offset")
            if not isinstance(value, int):
                return None
            return value
        except (json.JSONDecodeError, KeyError, ValueError, TypeError):
            return None

    def save_offset(self, offset: int) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"offset": offset}), encoding="utf-8")
        os.replace(tmp, self._path)
