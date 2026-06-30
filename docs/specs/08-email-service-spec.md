# Спецификация: Email-сервис (ai-mini-box-email)

> **Статус: ЗАКРЫТ** — Пакет `packages/email/` не реализован.
> IMAP/SMTP клиент, EmailDaemon, CLI — отсутствуют.
> Существуют только web API-прокладка (`routers/email.py`) и страница настроек (`EmailSettings.tsx`), которые возвращают заглушки.
> Если email-функциональность потребуется — spec требует полной реализации с нуля.

**Разработчик:** Email-разработчик

**Файлы:**
- `packages/email/ai_mini_box_email/__init__.py`
- `packages/email/ai_mini_box_email/config.py`
- `packages/email/ai_mini_box_email/imap_client.py`
- `packages/email/ai_mini_box_email/smtp_client.py`
- `packages/email/ai_mini_box_email/message_handler.py`
- `packages/email/ai_mini_box_email/daemon.py`
- `packages/email/ai_mini_box_email/plugin.py`
- `packages/email/pyproject.toml`

## 1. EmailConfig

```python
@dataclass
class EmailConfig:
    imap_host: str
    imap_port: int = 993
    imap_ssl: bool = True
    smtp_host: str
    smtp_port: int = 587
    smtp_ssl: bool = True
    email_address: str
    email_password: str
    poll_interval_seconds: int = 60
    folder: str = "INBOX"
    mark_as_seen: bool = True
    max_per_cycle: int = 50  # не более N писем за один poll
```

**Валидация (при старте daemon):**
- `imap_host`, `smtp_host`, `email_address`, `email_password` — обязательны
- Если хоть одно пустое — daemon не стартует, ошибка:
  ```
  Email не настроен. Выполните: ai-mini-box email config set ...
  ```

Хранение: `data/config.json`, зашифровано через Fernet (аналогично TelegramConfig).

## 2. ImapClient

```python
class ImapClient:
    def __init__(self, config: EmailConfig): ...
    def fetch_new(self) -> list[dict]:
        """Подключается к IMAP, ищет непрочитанные письма.
        Возвращает: [{ uid, from_addr, from_name, subject, body, date }]
        """
```

**Извлекаемые поля:** From (адрес + имя), Subject, Body (plain text из первой `text/plain` части), Date.

**Алгоритм:**
1. `IMAP4_SSL(imap_host, imap_port, timeout=30)` → `login()` → `select(folder)`
2. `search(None, "UNSEEN")`
3. Для каждого: `fetch(uid, "(RFC822)")` → `email.parser.BytesParser` → From, Subject, Body, Date
4. Если `mark_as_seen` — письмо помечается прочитанным
5. **Лимит:** `results[:self.config.max_per_cycle]` — остальные в следующем цикле (защита от 50 000 писем при первом запуске)
6. **Retry:** при ошибке — 3 попытки с exponential backoff (1s, 2s, 4s). После 3 неудач — лог ошибки, возврат `[]`

## 3. SmtpClient

```python
class SmtpClient:
    def __init__(self, config: EmailConfig): ...
    def send(self, to: str, subject: str, body: str) -> bool:
        """Отправляет email через SMTP."""
```

1. Subject с префиксом `Re:` (если ещё нет) — для reply-трединга
2. `SMTP(smtp_host, smtp_port, timeout=30)` → `starttls()` → `login()` → `send_message(MIMEText(...))`
3. **Retry:** 3 попытки с exponential backoff (1s, 2s, 4s). После 3 неудач — лог ошибки, возврат `False`

## 4. MessageHandler

```python
class MessageHandler:
    def __init__(self, contact_repo, message_repo): ...
    def handle(self, email_data: dict) -> Message:
        """
        1. Ищет контакт по email (contact_repo.find_by_email)
        2. Если нет — создаёт Contact(name=from_name, email=from_addr, source="email")
        3. Создаёт Message(source="email", external_id=uid, chat_id=from_addr,
                          contact_id=contact.id, text=body, received_at=date)
        4. Возвращает Message
        """
```

## 5. EmailDaemon

```python
class EmailDaemon:
    def __init__(self, config, handler, imap): ...
    def run(self):
        while self.running:
            # Загружаем конфиг каждый цикл (изменения через UI вступают сразу)
            config = load_email_config()

            try:
                for msg in self.imap.fetch_new():
                    self.handler.handle(msg)
            except Exception as e:
                logger.error("Email poll error: {}", e)
                time.sleep(10)

            time.sleep(self.config.poll_interval_seconds)
```

**Graceful shutdown:** SIGTERM/SIGINT → `self.running = False` → выход из цикла.

**Логирование по уровням:**

| Уровень | События |
|---|---|
| **INFO** | Старт/стоп демона, `Fetched 3 messages`, подключение к IMAP/SMTP |
| **WARNING** | Retry на 1-й/2-й попытке, пустой ответ IMAP, конфиг не полный |
| **ERROR** | 3/3 retry failed, IMAP/SMTP недоступен длительно, не удалось распарсить письмо |

```python
logger.add("logs/email.log", rotation="10 MB", level="DEBUG")
logger.add(sys.stderr, level="INFO")  # для Docker stdout
```

**EmailStatus (in-memory, для CLI status и API):**
```python
@dataclass
class EmailStatus:
    last_poll_at: Optional[datetime] = None
    last_error: Optional[str] = None
    connected: bool = False
    fetched_today: int = 0
```

## 6. Plugin registration

```python
# plugin.py
def register(app: typer.Typer):
    @app.command()
    def email(ctx: typer.Context): ...

    @email.command()
    def poll(): ...        # однократный poll

    @email.command()
    def daemon(): ...      # бесконечный цикл

    @email.command()
    def config(): ...      # show / set
```

**pyproject.toml:**
```toml
[project.entry-points."ai_mini_box.tools"]
email = "ai_mini_box_email.plugin:register"
```

Зависимости: только стандартная библиотека (`imaplib`, `smtplib`, `email`).

## 7. CLI-команды

```bash
ai-mini-box email config set imap_host imap.gmail.com
ai-mini-box email config set email_address my@email.com
ai-mini-box email config set email_password ****    # шифруется
ai-mini-box email config show

ai-mini-box email poll       # однократно
ai-mini-box email daemon     # фоновый процесс
```

## 8. Регистрация в ServiceRegistry

При старте `email daemon` зарегистрировать себя как `email_service` для доступа из API.

## 9. Что НЕ входит в v1 (отложено на 5.1)

- HTML-письма (только plain text)
- Вложения (картинки, PDF) — игнорировать
- Несколько email-аккаунтов
- IMAP IDLE (push-уведомления)
- Отправка писем из UI — только ответ на существующее сообщение
- Автоответчик / auto-reply

## 10. Тесты (новые)

**Graceful shutdown (2 теста):**
- `test_daemon_stops_on_sigterm` — запустить daemon в потоке, послать SIGTERM через `threading.Timer` + `os.kill`, проверить `"Daemon stopped"` в логе и exit code 0
- `test_daemon_stops_on_sigint` — то же с SIGINT (Ctrl+C)

**Лимит за цикл (1 тест):**
- `test_max_per_cycle` — mock IMAP возвращает 100 писем, `max_per_cycle=10`, `fetch_new()` возвращает 10

## 11. Критерии приёмки

- `ImapClient.fetch_new()` возвращает письма из IMAP
- `ImapClient.fetch_new()` не превышает `max_per_cycle`
- `SmtpClient.send()` отправляет письмо с корректным Subject (Re:)
- `MessageHandler.handle()` создаёт Contact + Message
- `EmailDaemon.run()` циклически опрашивает IMAP
- `EmailDaemon` завершается по SIGTERM/SIGINT (graceful shutdown)
- Конфиг перезагружается каждый цикл (изменения через UI вступают без перезапуска)
- CLI `email config set/show` работает с шифрованием
- `EmailStatus` обновляется после каждого цикла (last_poll_at, connected, fetched_today)
- Валидация: daemon не стартует без обязательных полей
- Retry: IMAP и SMTP — 3 попытки с exponential backoff
- Без внешних зависимостей (только stdlib)
- Ошибки подключения IMAP/SMTP не падают (graceful)
- Логи: `logs/email.log` (rotation 10MB) + stdout с разделением по уровням
