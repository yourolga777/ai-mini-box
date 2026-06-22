from collections.abc import Generator

from sqlalchemy.orm import Session

from ai_mini_box.core.container import RepoContainer
from ai_mini_box.infrastructure.database import get_db


def get_repos() -> Generator[RepoContainer, None, None]:
    with get_db() as session:
        yield RepoContainer(session)
