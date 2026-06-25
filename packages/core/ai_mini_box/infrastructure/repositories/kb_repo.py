from __future__ import annotations

import json
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_mini_box.core.exceptions import NotFoundError
from ai_mini_box.core.models import KnowledgeBaseItem, Topic
from ai_mini_box.core.repositories import KnowledgeBaseRepo
from ai_mini_box.infrastructure.mapping import kb_item_from_orm, kb_item_to_orm
from ai_mini_box.infrastructure.orm_models import KnowledgeBaseModel


class SqliteKnowledgeBaseRepo(KnowledgeBaseRepo):
    def __init__(self, session: Session):
        self.session = session

    def query(self):
        from ai_mini_box.core.repositories import QueryBuilder

        all_items = self.list(limit=10000)
        return QueryBuilder(all_items)

    def list(self, limit=20, offset=0, sort="created_at", **filters):
        stmt = select(KnowledgeBaseModel)
        for key, value in filters.items():
            if value is not None and hasattr(KnowledgeBaseModel, key):
                stmt = stmt.where(getattr(KnowledgeBaseModel, key) == value)
        stmt = stmt.order_by(getattr(KnowledgeBaseModel, sort).desc()).limit(limit).offset(offset)
        orm_objs = self.session.execute(stmt).scalars().all()
        return [kb_item_from_orm(o) for o in orm_objs]

    def get_by_id(self, id: int) -> Optional[KnowledgeBaseItem]:
        orm_obj = self.session.get(KnowledgeBaseModel, id)
        return kb_item_from_orm(orm_obj) if orm_obj else None

    def add(self, item: KnowledgeBaseItem) -> KnowledgeBaseItem:
        orm_obj = kb_item_to_orm(item)
        self.session.add(orm_obj)
        self.session.flush()
        self.session.refresh(orm_obj)
        return kb_item_from_orm(orm_obj)

    def update(self, item: KnowledgeBaseItem) -> KnowledgeBaseItem:
        orm_obj = self.session.get(KnowledgeBaseModel, item.id)
        if not orm_obj:
            raise NotFoundError("KnowledgeBaseItem", item.id)
        for field, value in item.model_dump(exclude_unset=True).items():
            if field == "question_keywords":
                value = json.dumps(value, ensure_ascii=False)
            setattr(orm_obj, field, value)
        self.session.flush()
        self.session.refresh(orm_obj)
        return kb_item_from_orm(orm_obj)

    def delete(self, id: int) -> bool:
        orm_obj = self.session.get(KnowledgeBaseModel, id)
        if not orm_obj:
            return False
        self.session.delete(orm_obj)
        self.session.flush()
        return True

    def search_by_topic(self, topic: Topic) -> list[KnowledgeBaseItem]:
        stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.topic == topic)
        orm_objs = self.session.execute(stmt).scalars().all()
        return [kb_item_from_orm(o) for o in orm_objs]

    def find_matching(self, text: str, topic: Optional[Topic] = None) -> list[KnowledgeBaseItem]:
        """
        Ищет записи, у которых question_keywords пересекаются с текстом.
        Сортировка по количеству совпадений (больше → выше).
        """
        text_words = set(text.lower().split())
        all_items = self.list(limit=10000)
        if topic:
            all_items = [i for i in all_items if i.topic == topic]

        scored = []
        for item in all_items:
            keywords = [kw.strip().lower() for kw in item.question_keywords if kw.strip()]
            if not keywords:
                continue
            match_count = len(text_words & set(keywords))
            if match_count > 0:
                scored.append((match_count, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored]
