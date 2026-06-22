from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_mini_box.core.exceptions import NotFoundError
from ai_mini_box.core.models import Contact
from ai_mini_box.core.repositories import ContactRepo
from ai_mini_box.infrastructure.mapping import contact_from_orm, contact_to_orm
from ai_mini_box.infrastructure.orm_models import ContactModel


class SqliteContactRepo(ContactRepo):
    def __init__(self, session: Session):
        self.session = session

    def query(self):
        from ai_mini_box.core.repositories import QueryBuilder
        all_items = self.list(limit=10000)
        return QueryBuilder(all_items)

    def list(self, limit=20, offset=0, sort="name", **filters):
        stmt = select(ContactModel)
        for key, value in filters.items():
            if value is not None and hasattr(ContactModel, key):
                stmt = stmt.where(getattr(ContactModel, key) == value)
        if sort and hasattr(ContactModel, sort):
            stmt = stmt.order_by(getattr(ContactModel, sort))
        stmt = stmt.limit(limit).offset(offset)
        orm_objs = self.session.execute(stmt).scalars().all()
        return [contact_from_orm(o) for o in orm_objs]

    def get_by_id(self, id: int) -> Optional[Contact]:
        orm_obj = self.session.get(ContactModel, id)
        return contact_from_orm(orm_obj) if orm_obj else None

    def add(self, contact: Contact) -> Contact:
        orm_obj = contact_to_orm(contact)
        self.session.add(orm_obj)
        self.session.flush()
        self.session.refresh(orm_obj)
        return contact_from_orm(orm_obj)

    def update(self, contact: Contact) -> Contact:
        orm_obj = self.session.get(ContactModel, contact.id)
        if not orm_obj:
            raise NotFoundError("Contact", contact.id)
        for field, value in contact.model_dump(exclude_unset=True).items():
            setattr(orm_obj, field, value)
        self.session.flush()
        self.session.refresh(orm_obj)
        return contact_from_orm(orm_obj)

    def delete(self, id: int) -> bool:
        orm_obj = self.session.get(ContactModel, id)
        if not orm_obj:
            return False
        self.session.delete(orm_obj)
        self.session.flush()
        return True

    def search(self, query: str) -> list[Contact]:
        q = query.lower()
        stmt = select(ContactModel)
        orm_objs = self.session.execute(stmt).scalars().all()
        return [
            contact_from_orm(o) for o in orm_objs
            if q in (o.name or "").lower()
            or q in (o.phone or "").lower()
            or q in (o.email or "").lower()
            or q in (o.telegram or "").lower()
        ]
