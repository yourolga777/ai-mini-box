# Order Detail UI

**Spec:** `docs/specs/05-frontend-order-detail-spec.md`

## Backend

### 1. `routers/order_items.py` — новый файл
- `GET /api/orders/{order_id}/items` → `OrderItemRepo.list_by_order(order_id)`
- `POST /api/orders/{order_id}/items` → создать `OrderItem` + `_recalc_total()` на репо
- `PUT /api/orders/{order_id}/items/{item_id}` → обновить поля + `_recalc_total()`
- `DELETE /api/orders/{order_id}/items/{item_id}` → удалить + `_recalc_total()`
- `PUT /api/orders/{order_id}` уже есть в `orders.py`

### 2. `routers/orders.py` — добавить
- `DELETE /api/orders/{item_id}` → удалить заказ и каскадно его позиции

### 3. `app.py` — зарегистрировать `order_items.router` с префиксом `/api/orders`

## Frontend

### 1. `api/client.ts`
- `getOrderItems(orderId)`
- `createOrderItem(orderId, data)`
- `updateOrderItem(orderId, itemId, data)`
- `deleteOrderItem(orderId, itemId)`
- `deleteOrder(id)`
- `updateOrder(id, data)`
- `searchProducts(query)`

### 2. `pages/OrderDetail.tsx` — новый
- Шапка: заголовок + статус-бейдж + селект смены статуса + кнопка «Удалить» (confirm)
- Блок контакта: ссылка на контакт или кнопка привязки
- Блок сообщения: ссылка на сообщение или «Создан вручную»
- Таблица позиций: товар, кол-во, цена, сумма, кнопка ×
- Итого: `sum(item.quantity * item.price_kopecks)`
- Кнопка «+ Добавить позицию» → модалка
- Модалка: поиск товара (автодополнение), поля (название, кол-во, цена)
- Заметки: textarea, автосохранение на blur
- Даты создания/обновления
- Состояния: skeleton / 404 / error / empty items

### 3. `pages/Orders.tsx`
- Строки → ссылки на `/orders/:id`
- Колонка «Клиент» вместо contact_id (запрос в `api.contacts`)
- Колонка «Дата» (`created_at`)
- Фильтр по статусу (select)
- Поиск по заметкам (search input)

### 4. `App.tsx` — роут `orders/:id`

## Complexity: 5 SP
