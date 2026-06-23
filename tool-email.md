# Инструмент: email

## Описание

Работа с Email-каналом: проверка подключения, однократный poll, отправка ответов.

Использует IMAP4_SSL для чтения и SMTP для отправки.

### Команда

```bash
ai-mini-box email COMMAND [OPTIONS]
```

### Подкоманды

| Команда | Описание |
|---------|----------|
| `test` | Проверить подключение к IMAP-серверу |
| `poll` | Прочитать непрочитанные письма (без обработки LLM) |
| `send` | Отправить письмо |
| `config` | Показать текущие настройки email |

### Опции для подкоманд

**`email test`:**
- `--config PATH` — путь к config.json

**`email poll`:**
- `--config PATH`
- `--limit N` — максимум писем (default: 10)
- `--json` — вывод в JSON
- `--raw` — показать тело письма (без MIME-парсинга)

**`email send`:**
- `--to EMAIL` — получатель (обязательно)
- `--subject TEXT` — тема письма
- `--body TEXT` — текст письма
- `--reply-to EMAIL` — Message-ID для reply (threading)

### Примеры

```bash
ai-mini-box email test
# → ✅ Connected to imap.yandex.ru:993 (ОК)

ai-mini-box email poll --json --limit 5
# → [{"from": "ivan@mail.ru", "subject": "Вопрос", "topic": "Цены"}, ...]

ai-mini-box email send --to "client@mail.ru" --subject "Re: Вопрос" --body "Здравствуйте..."
# → ✅ Sent to client@mail.ru
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `email` для работы с Email-каналом (IMAP + SMTP).

### Требования:
1. Используй Typer для CLI с подкомандами (Typer группой или `app.add_typer`)
2. Подкоманды:
   - `test`: IMAP-подключение → OK/FAIL
   - `poll`: поиск UNSEEN писем → список (from, subject, date, body)
   - `send`: отправка письма через SMTP (логин/пароль из config)
   - `config`: показать настройки email из config.json
3. Используй существующий `EmailChannel` из `infrastructure/channels/email_channel.py`:
   - Конструктор: `EmailChannel(imap_server, imap_port, login, password)`
   - Метод `connect()` → bool
   - Метод `poll()` → list[IncomingMessage]
   - Метод `send(to, subject, body)` → bool
4. Используй существующий `JsonConfigManager` для загрузки конфига
5. Пароль: расшифровка из Base64/DPAPI (есть в JsonConfigManager)
6. Флаг `--json` для структурированного вывода
7. Для `send`: обязательная проверка `--to` валидности email

### Архитектура:
- Файл: `ai_mini_box/tools/email.py`
- Регистрация: `def register(app: typer.Typer)` — `app.add_typer(email_app, name="email")`
- Использует `MessageRepo` из `ai_mini_box.core.repositories`
- Использует `JsonConfigManager` из `ai_mini_box.infrastructure.config`
- EmailChannel — в infrastructure/channels/email_channel.py
- Пароль расшифровывается через JsonConfigManager

### Тесты:
1. Unit: MockMessageRepo — poll сохраняет сообщения
2. Unit: send возвращает True
3. Unit: валидация email-адреса
4. Integration: CliRunner + mock канала — test → poll → send
5. Smoke: --help

### Структура файла:
```
tools/email.py
```

### Пример желаемого поведения:
```
$ ai-mini-box email test
✅ IMAP: Connected to imap.yandex.ru:993 (0.3s)

$ ai-mini-box email poll --limit 2
📧 1. От: ivan@mail.ru | Тема: "Цены" | Дата: 2026-06-20
📧 2. От: petr@yandex.ru | Тема: "Заказ #123" | Дата: 2026-06-21

$ ai-mini-box email send --to test@test.com --subject "Hello" --body "Test"
✅ Sent in 0.5s
```
```

