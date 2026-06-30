from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from ai_mini_box.core.exceptions import NotFoundError
from ai_mini_box.core.models import Order, OrderItem
from ai_mini_box.core.repositories import OrderItemRepo, OrderRepo, QueryBuilder
from ai_mini_box.infrastructure.mapping import (
    order_from_orm,
    order_item_from_orm,
    order_item_to_orm,
    order_to_orm,
)
from ai_mini_box.infrastructure.orm_models import OrderItemModel, OrderModel


class SqliteOrderRepo(OrderRepo):
    def __init__(self, session: Session):
        self.session = session

    def query(self) -> QueryBuilder:
        all_items = self.list(limit=10000)
        return QueryBuilder(all_items)

    def list(self, limit=20, offset=0, sort="created_at", **filters):
        stmt = select(OrderModel)
        for key, value in filters.items():
            if value is not None and hasattr(OrderModel, key):
                stmt = stmt.where(getattr(OrderModel, key) == value)
        if sort and hasattr(OrderModel, sort):
            stmt = stmt.order_by(getattr(OrderModel, sort))
        stmt = stmt.limit(limit).offset(offset)
        orm_objs = self.session.execute(stmt).scalars().all()
        return [order_from_orm(o) for o in orm_objs]

    def get_by_id(self, id: int) -> Optional[Order]:
        orm_obj = self.session.get(OrderModel, id)
        return order_from_orm(orm_obj) if orm_obj else None

    def add(self, order: Order) -> Order:
        orm_obj = order_to_orm(order)
        self.session.add(orm_obj)
        self.session.flush()
        self.session.refresh(orm_obj)
        return order_from_orm(orm_obj)

    def update(self, order: Order) -> Order:
        orm_obj = self.session.get(OrderModel, order.id)
        if not orm_obj:
            raise NotFoundError("Order", order.id)
        for field, value in order.model_dump(exclude_unset=True).items():
            setattr(orm_obj, field, value)
        self.session.flush()
        self.session.refresh(orm_obj)
        return order_from_orm(orm_obj)


class SqliteOrderItemRepo(OrderItemRepo):
    def __init__(self, session: Session):
        self.session = session

    def _recalc_total(self, order_id: int) -> None:
        total = self.session.execute(
            select(func.sum(OrderItemModel.quantity * OrderItemModel.price_kopecks))
            .where(OrderItemModel.order_id == order_id)
        ).scalar() or 0
        self.session.execute(
            update(OrderModel).where(OrderModel.id == order_id)
            .values(total_kopecks=total)
        )

    def list_by_order(self, order_id: int) -> list[OrderItem]:
        stmt = select(OrderItemModel).where(OrderItemModel.order_id == order_id)
        rows = self.session.execute(stmt).scalars().all()
        return [order_item_from_orm(r) for r in rows]

    def get_by_id(self, item_id: int) -> Optional[OrderItem]:
        row = self.session.get(OrderItemModel, item_id)
        return order_item_from_orm(row) if row else None

    def add(self, item: OrderItem) -> OrderItem:
        row = order_item_to_orm(item)
        self.session.add(row)
        self.session.flush()
        self.session.refresh(row)
        self._recalc_total(item.order_id)
        return order_item_from_orm(row)

    def update(self, item: OrderItem) -> OrderItem:
        row = self.session.get(OrderItemModel, item.id)
        if not row:
            raise NotFoundError("OrderItem", item.id)
        for field, value in item.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        self.session.flush()
        self.session.refresh(row)
        self._recalc_total(item.order_id)
        return order_item_from_orm(row)

    def delete(self, item_id: int) -> None:
        row = self.session.get(OrderItemModel, item_id)
        if not row:
            raise NotFoundError("OrderItem", item_id)
        order_id = row.order_id
        self.session.delete(row)
        self.session.flush()
        self._recalc_total(order_id)
