from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_mini_box.core.exceptions import NotFoundError
from ai_mini_box.core.models import Product
from ai_mini_box.core.repositories import ProductRepo
from ai_mini_box.infrastructure.mapping import product_from_orm, product_to_orm
from ai_mini_box.infrastructure.orm_models import ProductModel


class SqliteProductRepo(ProductRepo):
    def __init__(self, session: Session):
        self.session = session

    def query(self):
        from ai_mini_box.core.repositories import QueryBuilder
        all_items = self.list(limit=10000)
        return QueryBuilder(all_items)

    def list(self, limit=20, offset=0, sort="name", **filters):
        stmt = select(ProductModel)
        for key, value in filters.items():
            if value is not None and hasattr(ProductModel, key):
                stmt = stmt.where(getattr(ProductModel, key) == value)
        if sort and hasattr(ProductModel, sort):
            stmt = stmt.order_by(getattr(ProductModel, sort))
        stmt = stmt.limit(limit).offset(offset)
        orm_objs = self.session.execute(stmt).scalars().all()
        return [product_from_orm(o) for o in orm_objs]

    def get_by_id(self, id: int) -> Optional[Product]:
        orm_obj = self.session.get(ProductModel, id)
        return product_from_orm(orm_obj) if orm_obj else None

    def add(self, product: Product) -> Product:
        orm_obj = product_to_orm(product)
        self.session.add(orm_obj)
        self.session.flush()
        self.session.refresh(orm_obj)
        return product_from_orm(orm_obj)

    def update(self, product: Product) -> Product:
        orm_obj = self.session.get(ProductModel, product.id)
        if not orm_obj:
            raise NotFoundError("Product", product.id)
        for field, value in product.model_dump(exclude_unset=True).items():
            setattr(orm_obj, field, value)
        self.session.flush()
        self.session.refresh(orm_obj)
        return product_from_orm(orm_obj)

    def delete(self, id: int) -> bool:
        orm_obj = self.session.get(ProductModel, id)
        if not orm_obj:
            return False
        self.session.delete(orm_obj)
        self.session.flush()
        return True

    def search(self, query: str) -> list[Product]:
        q = query.lower()
        stmt = select(ProductModel)
        orm_objs = self.session.execute(stmt).scalars().all()
        return [
            product_from_orm(o) for o in orm_objs
            if q in (o.name or "").lower()
            or q in (o.description or "").lower()
            or q in (o.category or "").lower()
        ]
