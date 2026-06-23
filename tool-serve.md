# Инструмент: serve

## Описание

Запускает фоновый демон, который слушает Telegram и/или Email каналы, классифицирует входящие сообщения, генерирует черновики ответов и сохраняет историю в БД.

Это основной "рабочий" инструмент системы — аналог текущего `main.py`.

### Команда

```bash
ai-mini-box serve [OPTIONS]
```

### Опции

| Опция | Описание |
|-------|----------|
| `--config PATH` | Путь к config.json (default: data/config.json) |
| `--interval N` | Интервал polling в секундах (default: из config) |
| `--daemon` | Запуск в фоновом режиме (Windows: скрытое окно) |
| `--pidfile PATH` | Файл с PID процесса (для --daemon) |
| `--single-instance` | Проверка, что процесс уже запущен |
| `--no-email` | Отключить Email-канал |
| `--no-telegram` | Отключить Telegram-канал |
| `--once` | Однократный poll всех каналов и выход |
| `--dry-run` | Проверка подключения без обработки сообщений |
| `--verbose` | Подробное логирование в stdout |

### Примеры

```bash
ai-mini-box serve
# → [INFO] InboxService polling started. Press Ctrl+C to stop.

ai-mini-box serve --once
# → Polled 3 messages from Telegram, 1 from Email

ai-mini-box serve --dry-run
# → [Telegram] ✅ Connected (bot: MyShopBot)
# → [Email]    ✅ Connected (imap.yandex.ru)
# → [LLM]      ✅ Loaded (Phi-3-mini-q4.gguf)
# → Database: data/app.db

ai-mini-box serve --daemon --pidfile /tmp/ai-box.pid
# → [INFO] Daemon started, PID: 12345
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `serve` для запуска фонового демона обработки входящих сообщений.

### Требования:
1. Используй Typer для CLI
2. Основной компонент — `InboxService` из `service_layer/inbox_service.py`:
   - Конструктор: `InboxService(classifier, llm_provider, contact_repo, message_repo, channels, product_repo, config)`
   - Метод `poll_all()` — бесконечный цикл polling всех каналов
   - Метод `shutdown()` — остановка с сохранением состояния
3. Graceful shutdown: обработать Ctrl+C, SIGINT, SIGTERM
4. Single instance: через `ensure_single_instance` из `infrastructure/system/single_instance.py` (Win32 CreateMutexW)
5. Флаг `--daemon`: запуск в фоне (через python-daemon или subprocess)
6. Флаг `--dry-run`: проверить все подключения и выйти
7. Флаг `--once`: один poll-цикл, затем выход
8. Логирование через loguru (setup_logging из infrastructure/logging/setup.py)
9. Флаг `--pidfile`: сохранять PID для --daemon режима
10. Health-check: если канал отвалился — реконнект с exponential backoff

### Архитектура:
- Файл: `ai_mini_box/tools/serve.py`
- Регистрация: `def register(app: typer.Typer)` — одиночная команда
- Использует все репозитории: ContactRepo, ProductRepo, MessageRepo, OrderRepo
- Использует JsonConfigManager, get_db, setup_logging
- Каналы: TelegramChannel, EmailChannel (опционально WhatsAppChannel)
- Классификатор + LLM — внешние зависимости (lazy-load)
- Graceful shutdown: Ctrl+C → сохранение состояния
- Single instance: через мьютекс (Windows) / PID-файл (Linux)

### Тесты:
1. Unit: MockInboxService — poll_all → shutdown
2. Unit: обработка ошибок канала (reconnect)
3. Integration: CliRunner — --dry-run проверяет конфиг
4. Integration: CliRunner — --once однократный poll
5. Smoke: --help

### Структура файла:
```
tools/serve.py
```

### Пример желаемого поведения:
```
$ ai-mini-box serve --dry-run
[Telegram] ✅ Connected (bot: MyShopBot)
[Email]    ✅ Connected (imap.yandex.ru)
[LLM]      ✅ Loaded (Phi-3-mini)
Database: data/app.db

$ ai-mini-box serve --once
Polled 3 new messages: 2 classified, 1 draft generated

$ ai-mini-box serve
[INFO] InboxService polling started. Press Ctrl+C to stop.
[INFO] Processing message from @ivan: "Сколько стоит?" → Цены (0.97)
^C
[INFO] Shutdown complete
```
```

