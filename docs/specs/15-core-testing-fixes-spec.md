# Спецификация: Каркас — Исправления по результатам тестирования (v1)

**Разработчик:** Каркас (core — `ai_mini_box`)  
**Приоритет:** P0  
**Статус:** К реализации  

---

## Задача К-1: Analytics 500 — замена `cast(X, Date)` на `func.date(X)`

**Где:** `packages/web/ai_mini_box_web/routers/analytics.py`

### Проблема (root cause)

SQLite не поддерживает нативный тип `DATE`. Выражение `CAST(messages.received_at AS DATE)` приводит к **NUMERIC affinity**, которая для текстовых дат возвращает **целое число 0**. SQLAlchemy пытается вызвать `datetime.fromisoformat(0)` и падает с `TypeError: fromisoformat: argument must be str`. В результате — HTTP 500 на всех 5 эндпоинтах аналитики.

При этом в ядре (`packages/core/ai_mini_box/core/services/analytics.py`) уже используется правильный подход — `func.date()` — и там всё работает.

### Что сделать

**1. Заменить импорты:**
```python
# Было
from sqlalchemy import cast, Date, func, ...

# Стало
from sqlalchemy import func, ...
```

**2. Заменить все 13 использований по шаблону:**

| Строки | Было | Стало |
|---|---|---|
| 78, 82, 83 | `cast(MessageModel.received_at, Date)` | `func.date(MessageModel.received_at)` |
| 96, 100, 101 | `cast(OrderModel.created_at, Date)` | `func.date(OrderModel.created_at)` |
| 114, 121, 122 | `cast(OrderModel.created_at, Date)` | `func.date(OrderModel.created_at)` |
| 255, 262, 263 | `cast(OrderModel.created_at, Date)` | `func.date(OrderModel.created_at)` |
| 291 | `cast(MessageModel.received_at, Date)` | `func.date(MessageModel.received_at)` |

**3. Дополнительно: исправить валидацию `days=0`**

Фронтенд (`Dashboard.tsx:26`) отправляет `days=0` для "Всё время". Хендлер `analytics.py:46` имеет `days: int = Query(30, ge=1, le=3650)` — `ge=1` блокирует 0 с 422.

- Либо убрать `ge=1` (тогда `days=0` = вся история)
- Либо явно обработать `days <= 0` в теле функции как "без ограничения"

**4. Убрать неиспользуемый импорт `Date` из всех затронутых файлов** (если он больше нигде не нужен)

### Проверка

1. Перезапустить сервер
2. Проверить в браузере: `/api/analytics/messages?days=30` → JSON с массивом `{date, count}`
3. Проверить: `/api/analytics/orders`, `/api/analytics/revenue`, `/api/analytics/forecast`, `/api/analytics/retention`
4. Проверить `days=0` → возвращает данные без фильтра
5. Фронтенд Dashboard перестаёт показывать ошибки

### Acceptance criteria

- Все 5 эндпоинтов аналитики возвращают HTTP 200 с корректными данными
- В логах сервера нет `TypeError: fromisoformat`
- Dashboard загружается без ошибок
- `days=0` обрабатывается без 422
- Старые тесты проходят

---

## Границы ответственности (scope exclude)

- Не менять фронтенд (Dashboard.tsx, компоненты) — только бэкенд
- Не менять core-сервисы (`AnalyticsService` в ядре) — там уже правильно
- Не менять Telegram/LLM/Mail плагины
- Не менять API-контракты (формат ответа остаётся тем же)
