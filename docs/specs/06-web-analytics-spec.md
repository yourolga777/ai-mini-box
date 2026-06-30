# Спецификация: API эндпоинты аналитики

**Разработчик:** Бэкенд-разработчик (web)

**Файлы:**
- `packages/web/ai_mini_box_web/routers/analytics.py` — новый роутер
- `packages/web/ai_mini_box_web/server.py` — подключение роутера

## 1. Эндпоинты

| Метод | Path | Описание |
|---|---|---|
| `GET` | `/api/analytics/summary` | Базовые счётчики |
| `GET` | `/api/analytics/messages?days=30` | Сообщения по дням |
| `GET` | `/api/analytics/orders?days=30` | Заказы по дням |
| `GET` | `/api/analytics/revenue?days=30` | Выручка по дням |
| `GET` | `/api/analytics/channels` | Распределение по каналам |
| `GET` | `/api/analytics/top-contacts?limit=10` | Топ контактов |
| `GET` | `/api/analytics/funnel` | Воронка конверсии |
| `GET` | `/api/analytics/ltv` | LTV |
| `GET` | `/api/analytics/retention?days=90` | Retention |
| `GET` | `/api/analytics/forecast?days=30` | Прогноз |

## 2. Response format

```json
{
  "data": { ... },
  "meta": {
    "cached_at": "2026-06-27T12:00:00",
    "has_more": false,
    "error": null
  }
}
```

## 3. Кеширование

- In-memory cache через `cachetools.TTLCache`
- TTL: 5 минут
- Ключ: `f"analytics:{method_name}:{days}"`
- При ошибке — не кешировать

## 4. Graceful degradation

- `forecast` без sklearn: `data = null`, `meta.error = "scikit-learn not installed"`
- `ltv` без pandas: `data = null`, `meta.error = "pandas not installed"`

## 5. Подключение

```python
# server.py
from .routers.analytics import router as analytics_router
app.include_router(analytics_router, prefix="/api/analytics")
```

Роутер использует `get_repos` для получения сессии БД.

## 6. Критерии приёмки

- Все эндпоинты возвращают корректные данные
- Кеш работает (повторный запрос в течение 5 мин быстрее)
- `forecast` без sklearn → `meta.error`
- 200 OK всегда (ошибки в `meta.error`, не HTTP-статус)
- Таймаут запроса — 10 секунд (для сложных агрегаций)
