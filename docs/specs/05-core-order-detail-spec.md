# Спецификация: Модель OrderItem + репозиторий

**Разработчик:** Core-разработчик

**Файлы:**
- `packages/core/ai_mini_box/core/models.py`
- `packages/core/ai_mini_box/infrastructure/orm_models.py`
- `packages/core/ai_mini_box/infrastructure/mapping.py`
- `packages/core/ai_mini_box/core/repositories.py`
- `packages/core/ai_mini_box/infrastructure/repositories/order_repo.py`

## 1. Модель OrderItem

### 1.1 Pydantic модель

```python
class OrderItem(BaseModel):
    id: Optional[int] = None
    order_id: int
    product_id: Optional[int] = None
    product_name: str
    quantity: int = 1
    price_kopecks: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
```

- `product_id` — FK на Product (опционально)
- `product_name` — денормализация (название на момент заказа)
- `price_kopecks` — цена за единицу на момент заказа

### 1.2 ORM модель

```python
class OrderItemModel(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    product_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    price_kopecks = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.now)
```

- CASCADE delete при удалении заказа

### 1.3 Маппинг

```python
def order_item_to_orm(item: OrderItem) -> OrderItemModel:
def order_item_from_orm(row: OrderItemModel) -> OrderItem:
```

### 1.4 Репозиторий

```python
class OrderItemRepo(ABC):
    def list_by_order(self, order_id: int) -> list[OrderItem]: ...
    def get_by_id(self, item_id: int) -> OrderItem: ...
    def add(self, item: OrderItem) -> OrderItem: ...
    def update(self, item: OrderItem) -> OrderItem: ...
    def delete(self, item_id: int) -> None: ...

class SqliteOrderItemRepo(OrderItemRepo):
    # реализация через SQLAlchemy
```

### 1.5 Пересчёт total_kopecks

Метод `SqliteOrderItemRepo` (не модульная функция):

```python
class SqliteOrderItemRepo(OrderItemRepo):
    def __init__(self, session: Session):
        self.session = session

    def _recalc_total(self, order_id: int) -> None:
        """Вызывается после add / update / delete позиции."""
        total = self.session.execute(
            select(func.sum(OrderItemModel.quantity * OrderItemModel.price_kopecks))
            .where(OrderItemModel.order_id == order_id)
        ).scalar() or 0
        self.session.execute(
            update(OrderModel).where(OrderModel.id == order_id)
            .values(total_kopecks=total)
        )

    def add(self, item: OrderItem) -> OrderItem:
        row = order_item_to_orm(item)
        self.session.add(row)
        self.session.flush()
        self.session.refresh(row)
        self._recalc_total(item.order_id)
        return order_item_from_orm(row)

    # Аналогично update, delete
```

### 1.6 Регистрация в RepoContainer

Добавить `order_item_repo: OrderItemRepo` в `RepoContainer` (создаётся из `core/repositories.py`).

### 1.7 Миграция

```sql
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    product_name TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    price_kopecks INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 2. Критерии приёмки

- `OrderItemRepo.add()` создаёт запись и возвращает её с ID
- `OrderItemRepo.list_by_order()` возвращает все позиции заказа
- При добавлении позиции `total_kopecks` заказа пересчитывается
- При удалении позиции `total_kopecks` пересчитывается
- При удалении заказа позиции удаляются (CASCADE)
- `OrderItemRepo.get_by_id()` возвращает 404 при неверном ID
