# Спецификация: API эндпоинты OrderItem + доработка Order

**Разработчик:** Бэкенд-разработчик (web)

**Файлы:**
- `packages/web/ai_mini_box_web/routers/orders.py`
- `packages/web/ai_mini_box_web/dependencies.py` (RepoContainer — если нужно добавить order_item_repo)

## 1. Новые эндпоинты для OrderItem

| Метод | Path | Описание |
|---|---|---|
| `GET` | `/api/orders/{id}/items` | Список позиций заказа |
| `POST` | `/api/orders/{id}/items` | Добавить позицию |
| `PUT` | `/api/orders/{id}/items/{item_id}` | Обновить позицию |
| `DELETE` | `/api/orders/{id}/items/{item_id}` | Удалить позицию |

**`GET /api/orders/{id}/items`:**
```json
[
  {
    "id": 1,
    "order_id": 42,
    "product_id": 5,
    "product_name": "Ноутбук Lenovo ThinkPad",
    "quantity": 2,
    "price_kopecks": 7500000,
    "created_at": "2026-06-27T12:00:00"
  }
]
```

**`POST /api/orders/{id}/items`:**
```json
// Тело:
{
  "product_id": 5,
  "product_name": "Ноутбук Lenovo ThinkPad",
  "quantity": 2,
  "price_kopecks": 7500000
}
```

- Если `product_id` указан и продукт существует — `product_name` и `price_kopecks` берутся из Product
- Если `product_id` не указан — `product_name` обязателен
- После создания — пересчёт total

**`PUT /api/orders/{id}/items/{item_id}`:** обновление полей + пересчёт total

**`DELETE /api/orders/{id}/items/{item_id}`:** удаление + пересчёт total

## 2. Доработка существующих эндпоинтов

**`GET /api/orders/{id}` — расширенный ответ:**
```json
{
  "id": 42,
  "contact_id": 7,
  "status": "new",
  "total_kopecks": 15000000,
  "notes": "Срочная доставка",
  "source_message_id": 123,
  "created_at": "...",
  "updated_at": "...",
  "items": [
    { "id": 1, "product_name": "...", "quantity": 2, "price_kopecks": 7500000 }
  ],
  "contact_name": "Иван Петров"
}
```

- `items` — JOIN order_items
- `contact_name` — JOIN contacts

**`GET /api/orders?contact_id=...` — добавить `contact_name`:**
- JOIN с contacts, если контакт удалён — `contact_name = "Удалённый контакт"`

**`GET /api/orders` — добавить поиск:**
- `search` — LIKE по `notes`

**`PUT /api/orders/{id}` — валидация статуса:**
- Допустимые переходы: `new → processing`, `processing → completed`, `* → cancelled`
- Недопустимый переход → 400 Bad Request

## 3. Критерии приёмки

- Все 4 эндпоинта OrderItem работают (CRUD)
- После операций с позициями `total_kopecks` пересчитывается
- `GET /api/orders/{id}` возвращает items и contact_name
- `PUT /api/orders/{id}` проверяет допустимость перехода статуса
- `search` в списке заказов работает
- 404 при неверном order_id / item_id
