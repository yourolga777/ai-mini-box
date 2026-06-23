# Инструмент: whatsapp

## Описание

Работа с WhatsApp-каналом: проверка подключения, чтение сообщений, отправка ответов. Использует WhatsApp Business API (или библиотеку вроде baileys/venom). #1 канал коммуникации для малого бизнеса.

### Команда

```bash
ai-mini-box whatsapp COMMAND [OPTIONS]
```

### Подкоманды

| Команда | Описание |
|---------|----------|
| `test` | Проверить подключение к WhatsApp |
| `poll` | Получить новые сообщения |
| `send` | Отправить сообщение |
| `info` | Информация об аккаунте |

### Опции

**`whatsapp test`:**
- `--config PATH` — путь к config.json

**`whatsapp poll`:**
- `--limit N` — максимум сообщений (default: 10)
- `--json` — JSON-вывод

**`whatsapp send`:**
- `--to TEXT` — номер телефона в формате +7xxxxxxxxxx
- `--text TEXT` — текст сообщения
- `--template TEXT` — имя шаблона (для Business API)

### Примеры

```bash
ai-mini-box whatsapp test
# → ✅ WhatsApp Business API connected (account: MyShop)

ai-mini-box whatsapp poll --json --limit 5
# → [{"from": "+79991234567", "text": "Сколько стоит?", "date": "2026-06-21"}, ...]

ai-mini-box whatsapp send --to "+79991234567" --text "Здравствуйте!"
# → ✅ Sent to +79991234567
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `whatsapp` для работы с WhatsApp-каналом.

### Требования:
1. Typer с подкомандами: `test`, `poll`, `send`, `info`
2. Используй `WhatsAppChannel` (создать в infrastructure/channels/):
   - `connect()` → bool
   - `poll()` → list[IncomingMessage]
   - `send(phone, text)` → bool
3. Сообщения сохраняются через `MessageRepo` из `ai_mini_box.core.repositories`
4. Токен/ключ API из конфига (через `JsonConfigManager`)
5. `--json` для poll

### Архитектура:
- Файл: `ai_mini_box/tools/whatsapp.py`
- Регистрация: `def register(app: typer.Typer)`
- Импорты: только из `ai_mini_box.core`, `ai_mini_box.infrastructure`

### Тесты:
1. Unit: MockMessageRepo — poll сохраняет сообщения
2. Unit: send возвращает True при успехе
3. Integration: CliRunner + mock канала
4. Smoke: `--help` показывает подкоманды

### Пример желаемого поведения:
```
$ ai-mini-box whatsapp test
✅ WhatsApp connected (account: MyShop)

$ ai-mini-box whatsapp poll --limit 3
📨 1. +79991234567: "Сколько стоит доставка?" [11:30]
```
```

### Тесты

- `test_whatsapp.py` — 3 unit-теста
- `test_whatsapp_integration.py` — 1 интеграционный
