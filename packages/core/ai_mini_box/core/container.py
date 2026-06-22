from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session

from ai_mini_box.infrastructure.repositories import (
    SqliteContactRepo,
    SqliteMessageRepo,
    SqliteOrderRepo,
    SqliteProductRepo,
)


class RepoContainer:
    def __init__(self, session: Session):
        self._session = session
        self.contacts = SqliteContactRepo(session)
        self.products = SqliteProductRepo(session)
        self.messages = SqliteMessageRepo(session)
        self.orders = SqliteOrderRepo(session)


@dataclass
class AppContext:
    repos: RepoContainer
    config_path: str = "data/config.json"
    verbose: bool = False

    _instance: Optional["AppContext"] = field(default=None, repr=False)

    @classmethod
    def init(cls, repos: RepoContainer, **kwargs) -> "AppContext":
        cls._instance = cls(repos=repos, **kwargs)
        return cls._instance

    @classmethod
    def get(cls) -> "AppContext":
        if cls._instance is None:
            raise RuntimeError("AppContext not initialized. Call AppContext.init() first.")
        return cls._instance
