# Инструмент: sms

## Описание

SMS-канал: отправка уведомлений и сообщений клиентам через SMS-провайдера (Twilio, SMS-Центр, etc.). Только отправка (исходящие), чтение входящих SMS — опционально.

### Команда

```bash
ai-mini-box sms COMMAND [OPTIONS]
```

### Подкоманды

| Команда | Описание |
|---------|----------|
| `test` | Проверить подключение к SMS-провайдеру |
| `send` | Отправить SMS |
| `config` | Настройка SMS-провайдера |

### Опции

**`sms test`:**
- `--config PATH` — путь к config.json

**`sms send`:**
- `--to TEXT` — номер телефона (+7xxxxxxxxxx)
- `--text TEXT` — текст SMS
- `--from TEXT` — имя отправителя (если поддерживается)

**`sms config`:**
- `--provider [twilio|smsc|smsaero]` — провайдер
- `--api-key TEXT` — API-ключ
- `--api-secret TEXT` — секрет

### Примеры

```bash
ai-mini-box sms test
# → ✅ SMS provider connected (SMSC.ru)

ai-mini-box sms send --to "+79991234567" --text "Ваш заказ #12 готов!"
# → ✅ SMS sent to +79991234567

ai-mini-box sms config --provider twilio --api-key "ACxxx"
# → ✅ Twilio configured
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `sms` для отправки SMS.

### Требования:
1. Typer с подкомандами: `test`, `send`, `config`
2. Поддержка Twilio, SMSC.ru, SMSAero (через HTTP API)
3. Только отправка (inbound SMS опционально)
4. Сообщения логируются через MessageRepo (source=SMS)
5. Настройки провайдера — в config.json
6. Лимит длины SMS: 160 символов (с предупреждением при превышении)

### Архитектура:
- Файл: `ai_mini_box/tools/sms.py`
- Регистрация: `def register(app: typer.Typer)`
- Импорты: только из `ai_mini_box.core`, `ai_mini_box.infrastructure`

### Тесты:
1. Unit: MockMessageRepo — send сохраняет сообщение
2. Unit: предупреждение при длине >160 символов
3. Integration: CliRunner — config → test → send
4. Smoke: --help

### Пример желаемого поведения:
```
$ ai-mini-box sms send --to "+79991234567" --text "Заказ готов!"
✅ SMS sent to +79991234567
```
```

### Тесты

- `test_sms.py` — 2 unit-теста
- `test_sms_integration.py` — 1 интеграционный
