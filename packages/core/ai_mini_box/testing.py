from __future__ import annotations

from typing import Optional

from ai_mini_box.core.models import Contact, Message, Order, Product
from ai_mini_box.core.repositories import (
    ContactRepo,
    MessageRepo,
    OrderRepo,
    ProductRepo,
    QueryBuilder,
)


class _MemoryStore:
    def __init__(self):
        self._items: dict[int, object] = {}
        self._next_id = 1

    def _next(self):
        idx = self._next_id
        self._next_id += 1
        return idx

    def query(self):
        return QueryBuilder(list(self._items.values()))

    def get(self, id: int):
        return self._items.get(id)

    def add(self, item):
        item.id = self._next()
        self._items[item.id] = item
        return item

    def update(self, item):
        if item.id in self._items:
            self._items[item.id] = item
        return item

    def delete(self, id: int) -> bool:
        return self._items.pop(id, None) is not None


class MockContactRepo(ContactRepo):
    def __init__(self):
        self._store = _MemoryStore()

    def query(self) -> QueryBuilder:
        return self._store.query()

    def list(self, limit=20, offset=0, sort="name", **filters):
        q = self._store.query()
        return q.filter(**filters).sort(sort).offset(offset).limit(limit).all()

    def get_by_id(self, id: int) -> Optional[Contact]:
        return self._store.get(id)

    def add(self, contact: Contact) -> Contact:
        return self._store.add(contact)

    def update(self, contact: Contact) -> Contact:
        return self._store.update(contact)

    def delete(self, id: int) -> bool:
        return self._store.delete(id)

    def search(self, query: str) -> list[Contact]:
        return self._store.query().search(query, "name", "phone", "email").all()


class MockProductRepo(ProductRepo):
    def __init__(self):
        self._store = _MemoryStore()

    def query(self) -> QueryBuilder:
        return self._store.query()

    def list(self, limit=20, offset=0, sort="name", **filters):
        q = self._store.query()
        return q.filter(**filters).sort(sort).offset(offset).limit(limit).all()

    def get_by_id(self, id: int) -> Optional[Product]:
        return self._store.get(id)

    def add(self, product: Product) -> Product:
        return self._store.add(product)

    def update(self, product: Product) -> Product:
        return self._store.update(product)

    def delete(self, id: int) -> bool:
        return self._store.delete(id)

    def search(self, query: str) -> list[Product]:
        return self._store.query().search(query, "name", "description", "category").all()


class MockMessageRepo(MessageRepo):
    def __init__(self):
        self._store = _MemoryStore()

    def query(self) -> QueryBuilder:
        return self._store.query()

    def list(self, limit=20, offset=0, sort="received_at", **filters):
        q = self._store.query()
        return q.filter(**filters).sort(sort, reverse=True).offset(offset).limit(limit).all()

    def get_by_id(self, id: int) -> Optional[Message]:
        return self._store.get(id)

    def add(self, message: Message) -> Message:
        return self._store.add(message)

    def search(self, query: str, topic: Optional[str] = None) -> list[Message]:
        results = self._store.query().search(query, "text").all()
        if topic:
            results = [m for m in results if m.topic and m.topic.value == topic]
        return results


class MockOrderRepo(OrderRepo):
    def __init__(self):
        self._store = _MemoryStore()

    def query(self) -> QueryBuilder:
        return self._store.query()

    def list(self, limit=20, offset=0, sort="created_at", **filters):
        q = self._store.query()
        return q.filter(**filters).sort(sort, reverse=True).offset(offset).limit(limit).all()

    def get_by_id(self, id: int) -> Optional[Order]:
        return self._store.get(id)

    def add(self, order: Order) -> Order:
        return self._store.add(order)

    def update(self, order: Order) -> Order:
        return self._store.update(order)
