from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_mini_box.core.models import Message
from ai_mini_box.core.repositories import MessageRepo, QueryBuilder
from ai_mini_box.infrastructure.mapping import message_from_orm, message_to_orm
from ai_mini_box.infrastructure.orm_models import MessageModel


class SqliteMessageRepo(MessageRepo):
    def __init__(self, session: Session):
        self.session = session

    def query(self) -> QueryBuilder:
        all_items = self.list(limit=10000)
        return QueryBuilder(all_items)

    def list(self, limit=20, offset=0, sort="received_at", **filters):
        stmt = select(MessageModel)
        for key, value in filters.items():
            if value is not None and hasattr(MessageModel, key):
                stmt = stmt.where(getattr(MessageModel, key) == value)
        if sort and hasattr(MessageModel, sort):
            stmt = stmt.order_by(getattr(MessageModel, sort))
        stmt = stmt.limit(limit).offset(offset)
        orm_objs = self.session.execute(stmt).scalars().all()
        return [message_from_orm(o) for o in orm_objs]

    def get_by_id(self, id: int) -> Optional[Message]:
        orm_obj = self.session.get(MessageModel, id)
        return message_from_orm(orm_obj) if orm_obj else None

    def add(self, message: Message) -> Message:
        orm_obj = message_to_orm(message)
        self.session.add(orm_obj)
        self.session.flush()
        self.session.refresh(orm_obj)
        return message_from_orm(orm_obj)

    def search(self, query: str, topic: Optional[str] = None) -> list[Message]:
        q = query.lower()
        stmt = select(MessageModel)
        if topic is not None:
            from ai_mini_box.core.models import Topic
            stmt = stmt.where(MessageModel.topic == Topic(topic))
        stmt = stmt.order_by(MessageModel.received_at.desc())
        orm_objs = self.session.execute(stmt).scalars().all()
        return [
            message_from_orm(o) for o in orm_objs
            if q in (o.text or "").lower()
        ]
