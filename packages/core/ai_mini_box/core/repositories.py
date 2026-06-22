from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

from .models import Contact, Message, Order, Product


class QueryBuilder:
    def __init__(self, items: list):
        self._items = items

    def filter(self, **kwargs) -> "QueryBuilder":
        result = self._items
        for key, value in kwargs.items():
            if value is not None:
                result = [i for i in result if getattr(i, key, None) == value]
        return QueryBuilder(result)

    def search(self, query: str, *fields: str) -> "QueryBuilder":
        if not query:
            return self
        q = query.lower()
        result = [
            i for i in self._items
            if any(q in (getattr(i, f, "") or "").lower() for f in fields)
        ]
        return QueryBuilder(result)

    def sort(self, key: str, reverse: bool = False) -> "QueryBuilder":
        self._items.sort(key=lambda i: getattr(i, key, "") or "", reverse=reverse)
        return self

    def limit(self, n: int) -> "QueryBuilder":
        return QueryBuilder(self._items[:n])

    def offset(self, n: int) -> "QueryBuilder":
        return QueryBuilder(self._items[n:])

    def all(self) -> list:
        return self._items

    def first(self) -> Any:
        return self._items[0] if self._items else None

    def count(self) -> int:
        return len(self._items)


class ContactRepo(ABC):
    @abstractmethod
    def query(self) -> QueryBuilder:
        ...

    @abstractmethod
    def list(self, limit: int = 20, offset: int = 0, sort: str = "name", **filters) -> list[Contact]:
        ...

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Contact]:
        ...

    @abstractmethod
    def add(self, contact: Contact) -> Contact:
        ...

    @abstractmethod
    def update(self, contact: Contact) -> Contact:
        ...

    @abstractmethod
    def delete(self, id: int) -> bool:
        ...

    @abstractmethod
    def search(self, query: str) -> list[Contact]:
        ...


class ProductRepo(ABC):
    @abstractmethod
    def query(self) -> QueryBuilder:
        ...

    @abstractmethod
    def list(self, limit: int = 20, offset: int = 0, sort: str = "name", **filters) -> list[Product]:
        ...

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Product]:
        ...

    @abstractmethod
    def add(self, product: Product) -> Product:
        ...

    @abstractmethod
    def update(self, product: Product) -> Product:
        ...

    @abstractmethod
    def delete(self, id: int) -> bool:
        ...

    @abstractmethod
    def search(self, query: str) -> list[Product]:
        ...


class MessageRepo(ABC):
    @abstractmethod
    def query(self) -> QueryBuilder:
        ...

    @abstractmethod
    def list(self, limit: int = 20, offset: int = 0, sort: str = "received_at", **filters) -> list[Message]:
        ...

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Message]:
        ...

    @abstractmethod
    def add(self, message: Message) -> Message:
        ...

    @abstractmethod
    def search(self, query: str, topic: Optional[str] = None) -> list[Message]:
        ...


class OrderRepo(ABC):
    @abstractmethod
    def query(self) -> QueryBuilder:
        ...

    @abstractmethod
    def list(self, limit: int = 20, offset: int = 0, sort: str = "created_at", **filters) -> list[Order]:
        ...

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Order]:
        ...

    @abstractmethod
    def add(self, order: Order) -> Order:
        ...

    @abstractmethod
    def update(self, order: Order) -> Order:
        ...


@dataclass
class RepoContainer:
    contacts: ContactRepo
    products: ProductRepo
    messages: MessageRepo
    orders: OrderRepo
