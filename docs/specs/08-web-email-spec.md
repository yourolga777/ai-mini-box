# Спецификация: Email API + PluginManager

**Разработчик:** Бэкенд-разработчик (web)

**Файлы:**
- `packages/web/ai_mini_box_web/routers/email.py` — новый роутер
- `packages/web/ai_mini_box_web/server.py` — подключение
- `packages/web/ai_mini_box_web/services/plugin_manager.py` — доработка

## 1. API эндпоинты

| Метод | Path | Описание |
|---|---|---|
| `GET` | `/api/email/status` | Статус email-плагина |
| `POST` | `/api/email/test` | Тестовое подключение |
| `POST` | `/api/email/poll` | Принудительная проверка |

**`GET /api/email/status`:**
```json
{
  "configured": true,
  "connected": true,
  "last_poll_at": "2026-06-27T12:00:00",
  "messages_fetched_today": 5,
  "error": null
}
```

**`POST /api/email/test`:**
```json
// Тело:
{ "imap_host": "imap.gmail.com", "imap_port": 993,
  "smtp_host": "smtp.gmail.com", "smtp_port": 587,
  "email_address": "test@gmail.com", "email_password": "****" }
// Ответ:
{ "success": true, "imap": true, "smtp": true, "message": null }
```

**`POST /api/email/poll`:**
Возвращает количество обработанных писем:
```json
{ "processed": 3 }
```

## 2. Интеграция с PluginManager

Добавить поддержку email в `PluginManager` (по аналогии с Telegram):

```python
pm.start("email")   # Popen daemon
pm.stop("email")    # kill PID
pm.status("email")  # PID, uptime
```

## 3. Подключение в server.py

```python
from .routers.email import router as email_router
app.include_router(email_router, prefix="/api/email")
```

## 4. Критерии приёмки

- `GET /api/email/status` возвращает статус (даже если не настроен)
- `POST /api/email/test` проверяет подключение
- `POST /api/email/poll` запускает однократный poll
- PluginManager управляет email-демоном (start/stop/status)
- Если email-плагин не установлен — `configured: false`
- Graceful degradation: роутер не падает при отсутствии пакета
