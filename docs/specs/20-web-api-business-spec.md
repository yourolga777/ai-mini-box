# Спецификация: Web API — Бизнес-конфиг и чатбот-эндпоинты (v2)

> **Статус: РЕАЛИЗОВАНО** (с отклонениями):
> - `?sort=need_human:desc` — добавлен параметр `sort` с поддержкой `sort=need_human:desc`
> - Ответы от `GET /api/messages` и `GET /api/messages/{id}` содержат все поля Pydantic-модели (включая новые)
> - Остальные endpoint'ы реализованы полностью

**Разработчик:** Веб (backend — FastAPI routers)  
**Приоритет:** P1  
**Статус:** К реализации  
**Зависит от:** 22-core (BusinessConfig, OrderService)

---

## 1. BusinessConfig CRUD

**Новый файл:** `packages/web/ai_mini_box_web/routers/business.py`

### GET /api/business/config

Возвращает текущий `BusinessConfig` из `data/business_config.json`.

```json
{
  "company_name": "...",
  "work_hours": "...",
  "delivery_info": "...",
  "return_policy": "...",
  "payment_methods": "...",
  "contacts": "...",
  "faq": [
    {"question": "...", "answer": "..."}
  ]
}
```

### PUT /api/business/config

Обновляет BusinessConfig. Принимает полный или частичный объект. Возвращает обновлённый конфиг.

**Валидация:** через Pydantic `BusinessConfig`.

### Регистрация в server.py

```python
app.include_router(business.router, prefix="/api/business", tags=["business"])
```

## 2. Reproduce chatbot processing

### POST /api/messages/{id}/reprocess-chatbot

Перезапустить обработку сообщения через ChatbotService (для ручной корректировки).

```json
// Request: optional
{}

// Response:
{
  "success": true,
  "category": "ЗАКАЗ",
  "subcategory": "доставка",
  "reply_to_user": "...",
  "need_human": false,
  "auto_replied": true
}
```

Логика:
1. Загрузить сообщение по ID
2. Загрузить BusinessConfig
3. Вызвать `get_service("chatbot").process_message(...)`
4. Сохранить результат на сообщение
5. Ответить результатом

Если `chatbot` сервис не зарегистрирован → 400 `{"error": "Chatbot service not available (LLM plugin not installed)"}`

## 3. Новые поля в ответах API сообщений

**Файл:** `packages/web/ai_mini_box_web/routers/messages.py`

В `GET /api/messages` и `GET /api/messages/{id}` добавить в ответ поля:
- `category`
- `subcategory`
- `need_human`
- `auto_replied`
- `auto_reply_text`
- `operator_context`

Добавить фильтр `?need_human=true` в GET /api/messages — показывать только сообщения, требующие оператора.

Добавить сортировку `?sort=need_human:desc` — сообщения с флагом наверху.

## 4. Фильтр по категории

Добавить `?category=ЗАКАЗ&category=ЖАЛОБА` — фильтр по категории чатбота (OR, любое из указанных).

## 5. Create order from message

### POST /api/orders/from-message

Создать заказ из сообщения (использует `OrderService.create_from_message()`).

```json
// Request:
{"message_id": 42, "contact_id": 7, "total_kopecks": 150000, "notes": "..."}

// Response:
{"id": 10, "status": "new", "total_kopecks": 150000}
```

## Acceptance criteria

- `GET /api/business/config` возвращает актуальный конфиг
- `PUT /api/business/config` обновляет конфиг, сохраняет в JSON
- `POST /api/messages/{id}/reprocess-chatbot` перезапускает обработку
- В ответах сообщений присутствуют все 6 новых полей
- Фильтр `?need_human=true` работает
- Фильтр `?category=ЗАКАЗ` работает
- Если LLM не установлен — эндпоинты возвращают понятную ошибку, не 500

## Scope exclude

- Не писать ChatbotService
- Не менять Telegram handler
- Не писать фронтенд
