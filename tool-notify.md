# Инструмент: notify

## Описание

Система уведомлений владельца бизнеса о важных событиях: новый заказ, жалоба клиента, ошибка канала связи. Отправляет через Telegram, Email или SMS в зависимости от настроек.

### Команда

```bash
ai-mini-box notify COMMAND [OPTIONS]
```

### Подкоманды

| Команда | Описание |
|---------|----------|
| `test` | Проверить каналы уведомлений |
| `send` | Отправить тестовое уведомление |
| `config` | Настроить каналы уведомлений |

### Опции

**`notify send`:**
- `--channel [telegram|email|sms|all]` — канал отправки
- `--message TEXT` — текст уведомления

**`notify config`:**
- `--on-order` — уведомлять при новом заказе (True/False)
- `--on-complaint` — уведомлять при жалобе (True/False)
- `--on-error` — уведомлять при ошибках демона (True/False)

### Примеры

```bash
ai-mini-box notify test
# → [Telegram] ✅ configured (bot: MyShopBot)
#   [Email]    ✅ configured (imap.yandex.ru)
#   [SMS]      ❌ Not configured

ai-mini-box notify send --channel telegram --message "Новый заказ #15"
# → ✅ Notification sent via Telegram

ai-mini-box notify config --on-order True --on-complaint True
# → ✅ Notifications: order=True, complaint=True, error=False
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `notify` для уведомлений владельца.

### Требования:
1. Typer с подкомандами: `test`, `send`, `config`
2. Используй `NotificationService` (создать в core/services/):
   - `send(channel, message) → bool`
   - `test_channels() → dict[str, bool]`
3. Каналы: Telegram (через TelegramChannel), Email (через EmailChannel), SMS (через SmsProvider)
4. Настройки хранятся в config.json (добавить поле notifications)
5. `notify config` — изменяет настройки через JsonConfigManager
6. При ошибке отправки — логировать через loguru, не падать

### Архитектура:
- Файл: `ai_mini_box/tools/notify.py`
- Регистрация: `def register(app: typer.Typer)`
- Импорты: только из `ai_mini_box.core`, `ai_mini_box.infrastructure`

### Тесты:
1. Unit: MockNotificationService — send возвращает True
2. Unit: config сохраняет настройки
3. Integration: CliRunner + tmp config — test всех каналов
4. Smoke: `--help`

### Пример желаемого поведения:
```
$ ai-mini-box notify test
[Telegram] ✅ Connected
[Email]    ✅ Connected
```
```

### Тесты

- `test_notify.py` — 2 unit-теста
- `test_notify_integration.py` — 1 интеграционный
