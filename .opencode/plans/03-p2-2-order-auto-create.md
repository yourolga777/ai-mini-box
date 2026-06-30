# Спецификация P2-2 — Auto-создание заказов из сообщений

## Связанные пункты

- Бэкенд: `01-backend-spec.md` → **P2-2** (Auto-создание заказов из сообщений)
- Фронтенд: `00-frontend-spec.md` → **P2-2** (Order UI в MessageDetail и ContactDetail)

---

## 1. Бэкенд

### 1.1 Message: новое поле `extracted_order_id`

**Файлы:**
- `packages/core/ai_mini_box/core/models.py` — `Message`: добавить `extracted_order_id: Optional[int] = None`
- `packages/core/ai_mini_box/infrastructure/orm_models.py` — `MessageOrm`: добавить колонку `extracted_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)`
- `packages/core/ai_mini_box/infrastructure/mapping.py` — маппинг для `extracted_order_id`

### 1.2 AutoProcessor: создание заказа

**Файл:** `packages/core/ai_mini_box/core/services/auto_processor.py`

После блока `extract_entities` (создание Task) добавить:

```python
order_info = self.llm.extract_order_info(message.text)
if order_info and order_info.get("is_order") and order_info.get("confidence", 0) >= 0.5:
    order = Order(
        contact_id=message.contact_id,
        source_message_id=message.id,
        total_kopecks=order_info.get("price_kopecks", 0),
        notes=message.text,
        status="new",
    )
    created = self.order_repo.add(order)
    message.extracted_order_id = created.id
    self.message_repo.update(message)
    result.order_created = True
```

Добавить поле в `AutoProcessResult`:
```python
@dataclass
class AutoProcessResult:
    task_created: bool = False
    order_created: bool = False
    category_id: Optional[int] = None
```

**Зависимость:** `AutoProcessor` нужен доступ к `self.order_repo`. Если конструктор `AutoProcessor` не принимает `order_repo` — передать через DI.

### 1.3 Миграция БД

Новая миграция (alembic или прямой SQL в `_ensure_tables`):

```sql
ALTER TABLE messages ADD COLUMN extracted_order_id INTEGER REFERENCES orders(id);
```

### 1.4 Новые эндпоинты

**Файл:** `packages/web/ai_mini_box_web/routers/messages.py`

**`GET /api/messages/{id}/order`:**
```python
@router.get("/{id}/order")
def get_message_order(id: int):
    msg = message_repo.get(id)
    if not msg:
        raise HTTPException(404, detail="Message not found")
    if not msg.extracted_order_id:
        return None
    order = order_repo.get(msg.extracted_order_id)
    return order
```

**`POST /api/messages/{id}/create-order`:**
```python
class CreateOrderRequest(BaseModel):
    total_kopecks: int = 0
    notes: str = ""

@router.post("/{id}/create-order")
def create_message_order(id: int, body: CreateOrderRequest):
    msg = message_repo.get(id)
    if not msg:
        raise HTTPException(404, detail="Message not found")
    if msg.extracted_order_id is not None:
        raise HTTPException(409, detail="Order already exists for this message")
    if msg.contact_id is None:
        raise HTTPException(400, detail="Cannot create order without a contact")

    order = Order(
        contact_id=msg.contact_id,
        source_message_id=msg.id,
        total_kopecks=body.total_kopecks,
        notes=body.notes or msg.text,
        status="new",
    )
    created = order_repo.add(order)
    msg.extracted_order_id = created.id
    message_repo.update(msg)
    return created
```

**`GET /api/orders?contact_id={contactId}` — проверить, существует ли такой эндпоинт.**

**Критерии приёмки:**
- `AutoProcessor.process()` создаёт `Order` для сообщения, где LLM распознала заказ
- Созданный заказ имеет `source_message_id = message.id`
- `GET /api/messages/{id}/order` возвращает созданный заказ (или null)
- `POST /api/messages/{id}/create-order` создаёт заказ вручную
- Повторный `POST` — 409 Conflict
- Создание без контакта — 400 Bad Request
- Существующие тесты проходят

---

## 2. Фронтенд

### 2.1 API client — новые методы

**Файл:** `packages/web/frontend/src/api/client.ts`

```typescript
getMessageOrder: (id: number) =>
  request<Order | null>(`/api/messages/${id}/order`),
createOrder: (id: number, data: { total_kopecks?: number; notes?: string }) =>
  request<Order>(`/api/messages/${id}/create-order`, { method: "POST", body: JSON.stringify(data) }),
getContactOrders: (contactId: number) =>
  request<Order[]>(`/api/orders?contact_id=${contactId}`),
```

**Order type:**
```typescript
export interface Order {
  id: number;
  contact_id: number | null;
  source_message_id: number | null;
  total_kopecks: number;
  notes: string;
  status: string;
  created_at: string;
}
```

### 2.2 MessageDetail — блок заказа

**Файл:** `packages/web/frontend/src/pages/MessageDetail.tsx`

**Вставить блок между ContactLink и Reply:**

```tsx
{/* Блок заказа */}
{orderLoading ? (
  <p>Загрузка...</p>
) : linkedOrder ? (
  <div className="border rounded p-4 mb-4">
    <h3 className="font-bold">Заказ #{linkedOrder.id}</h3>
    <p>Статус: {statusLabel(linkedOrder.status)}</p>
    <p>Сумма: {formatPrice(linkedOrder.total_kopecks)}</p>
    <a href={`/orders/${linkedOrder.id}`} className="text-blue-600">Открыть заказ →</a>
  </div>
) : (
  <button onClick={() => setShowCreateOrder(true)} className="...">
    Создать заказ
  </button>
)}
```

**Модалка создания заказа:**
- Поле «Сумма (коп.)» — number input, необязательное
- Поле «Примечание» — textarea, предзаполнено текстом сообщения
- Кнопка «Создать» → `POST /api/messages/{id}/create-order`
- При успехе: закрыть модалку, показать карточку заказа
- При ошибке: toast
- Если `contact_id === null`: показать сообщение «Сначала привяжите сообщение к контакту»

### 2.3 ContactDetail — блок заказов

**Файл:** `packages/web/frontend/src/pages/ContactDetail.tsx`

**Добавить секцию после чат-диалога:**

```tsx
<section className="mt-8">
  <h2 className="text-lg font-bold mb-2">Заказы</h2>
  {ordersLoading ? (
    <p>Загрузка...</p>
  ) : orders.length === 0 ? (
    <p className="text-gray-500">Нет заказов</p>
  ) : (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b">
          <th className="text-left py-2">ID</th>
          <th className="text-left py-2">Статус</th>
          <th className="text-left py-2">Сумма</th>
          <th className="text-left py-2">Дата</th>
        </tr>
      </thead>
      <tbody>
        {orders.map(order => (
          <tr key={order.id} className="border-b">
            <td className="py-2"><Link to={`/orders/${order.id}`}>#{order.id}</Link></td>
            <td className="py-2">{statusLabel(order.status)}</td>
            <td className="py-2">{formatPrice(order.total_kopecks)}</td>
            <td className="py-2">{formatDate(order.created_at)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )}
</section>
```

### 2.4 Форматирование

**Файл:** `packages/web/frontend/src/pages/helpers.ts` (или внутри `utils.ts`)

```typescript
export function formatPrice(kopecks: number): string {
  return `${(kopecks / 100).toLocaleString("ru-RU", { minimumFractionDigits: 2 })} ₽`;
}

export function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    new: "Новый",
    processing: "В обработке",
    completed: "Выполнен",
    cancelled: "Отменён",
  };
  return labels[status] ?? status;
}
```

### 2.5 Проверить роут /orders/:id

**Файл:** `packages/web/frontend/src/App.tsx`

- Добавить роут `<Route path="/orders/:id" element={<OrderDetail />} />` если его нет
- Создать компонент/страницу-заглушку `OrderDetail.tsx` (или редирект, если страницы заказов нет в рамках P2-2 — уточнить)

---

## 3. Тесты

### Бэкенд

**Файл:** `packages/web/tests/test_api_llm.py` (добавить класс `TestOrders`):

- `test_get_message_order_null` — сообщение без заказа → null/204
- `test_get_message_order_exists` — сообщение с extracted_order_id → Order
- `test_get_message_order_404` — несуществующее сообщение → 404
- `test_create_order_success` — ручное создание → 200
- `test_create_order_duplicate` — повторное создание → 409
- `test_create_order_no_contact` — сообщение без контакта → 400
- `test_create_order_message_404` — несуществующее сообщение → 404

### Фронтенд

- Визуальная проверка: все состояния (loading, order exists, no order, creating, error)
- Табы + кнопки переключаются корректно
- После создания — карточка появляется без F5

---

## 4. Архитектурные заметки

- `SqliteOrderRepo.add()` уже существует, не трогать
- Поле `extracted_order_id` — только для ручного создания, LLM-блок идёт опционально
- Если LLM плагин не установлен — `extract_order_info` не вызвать; `AutoProcessor` проверит наличие LLM
- Роут `/api/orders?contact_id=` уже может существовать — проверить
- `MessageDetail.tsx` уже имеет query для сообщения, блок заказа — вложенный useQuery от `message.id`
- ContactDetail загружает сообщения контакта, блок заказов — отдельный useQuery от `contactId`
