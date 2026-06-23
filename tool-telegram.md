# Инструмент: telegram

## Описание

Работа с Telegram-каналом: проверка бота, чтение сообщений, отправка ответов, настройка webhook.

### Команда

```bash
ai-mini-box telegram COMMAND [OPTIONS]
```

### Подкоманды

| Команда | Описание |
|---------|----------|
| `test` | Проверить подключение Telegram-бота |
| `poll` | Получить новые сообщения (getUpdates) |
| `send` | Отправить сообщение в чат |
| `set-webhook` | Установить webhook URL |
| `delete-webhook` | Удалить webhook |
| `info` | Информация о боте |

### Опции для подкоманд

**`telegram test`:**
- `--token TEXT` — токен бота (или из config)

**`telegram poll`:**
- `--limit N` — максимум сообщений (default: 10)
- `--json` — вывод в JSON
- `--offset N` — пропустить N сообщений

**`telegram send`:**
- `--chat-id INT` — ID чата (обязательно)
- `--text TEXT` — текст сообщения

**`telegram set-webhook`:**
- `--url TEXT` — URL webhook
- `--drop-pending` — удалить ожидающие обновления

### Примеры

```bash
ai-mini-box telegram test
# → ✅ Bot @MyShopBot connected (name: My Shop Bot)

ai-mini-box telegram poll --json --limit 3
# → [{"from": "@ivan", "text": "Сколько стоит?", "date": "2026-06-21"}, ...]

ai-mini-box telegram send --chat-id 123456 --text "Здравствуйте!"
# → ✅ Sent to chat 123456
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `telegram` для работы с Telegram-ботом.

### Требования:
1. Типизированный Typer с подкомандами
2. Подкоманды:
   - `test`: проверить токен и получить информацию о боте (BotFather)
   - `poll`: getUpdates через python-telegram-bot, сохранять offset
   - `send`: отправить сообщение в указанный chat-id
   - `set-webhook` / `delete-webhook`: управление webhook
   - `info`: инфо о боте (имя, username, id, кол-во чатов)
3. Используй существующий `TelegramChannel` из `infrastructure/channels/telegram_channel.py`:
   - Конструктор: `TelegramChannel(token, offset_repo=None)`
   - Метод `connect()` → bool
   - Метод `poll()` → list[IncomingMessage]
   - Метод `send(chat_id, text)` → bool
4. Для offset: `TelegramStateRepo` из `infrastructure/database/repositories/telegram_state_repo.py`
5. Токен можно передать аргументом или брать из config.json
6. Флаг `--json` для poll и info
7. Для `send` проверять, что чат существует (sendMessage с verify)

### Архитектура:
- Файл: `ai_mini_box/tools/telegram.py`
- Регистрация: `def register(app: typer.Typer)` — `app.add_typer(telegram_app, name="telegram")`
- Использует `MessageRepo` из `ai_mini_box.core.repositories`
- Использует `JsonConfigManager` для токена
- TelegramChannel — в infrastructure/channels/telegram_channel.py
- Сохраняет offset через MessageRepo (external_id)

### Тесты:
1. Unit: MockMessageRepo — poll сохраняет offset
2. Unit: send проверяет chat_id
3. Integration: CliRunner + mock канала — test → poll → send
4. Smoke: --help

### Структура файла:
```
tools/telegram.py
```

### Пример желаемого поведения:
```
$ ai-mini-box telegram test
✅ Bot @MyShopBot (ID: 123456789) is active

$ ai-mini-box telegram poll --limit 5
📨 1. @ivan (chat 98765): "Сколько стоит доставка?" [11:30]
📨 2. @petr (chat 87654): "Хочу заказать" [11:32]

$ ai-mini-box telegram send --chat-id 98765 --text "Добрый день!"
✅ Message sent
```
```

