# Инструмент: config

## Описание

Управление конфигурацией: просмотр, изменение, валидация настроек. Работает с `data/config.json`.

Пароль email хранится зашифрованным (Windows DPAPI с fallback на Base64). Инструмент позволяет безопасно обновлять настройки без ручного редактирования JSON.

### Команда

```bash
ai-mini-box config COMMAND [OPTIONS]
```

### Подкоманды

| Команда | Описание |
|---------|----------|
| `show` | Показать конфигурацию |
| `get` | Получить значение ключа |
| `set` | Установить значение |
| `check` | Проверить конфигурацию |
| `reset` | Сбросить до значений по умолчанию |

### Опции

**`config show`:**
- `--json` — вывод в JSON
- `--secrets` — показать пароли (по умолчанию скрыты)

**`config get`:**
- `KEY` — путь к ключу через точку (например: `telegram.token`, `llm.n_ctx`)

**`config set`:**
- `KEY` — путь к ключу
- `VALUE` — значение

**`config check`:**
- Без опций — проверка всех подключений
- `--telegram` | `--email` — только конкретный канал

### Примеры

```bash
ai-mini-box config show
# → telegram.token: *** (скрыт)
#   email.imap_server: imap.yandex.ru
#   llm.model_path: models/Phi-3-mini-q4.gguf
#   poll_interval: 30

ai-mini-box config show --json --secrets
# → {"telegram": {"token": "123:ABC"}, "email": {...}, ...}

ai-mini-box config get telegram.token
# → 123456:ABCdefGHIjklMNO

ai-mini-box config set poll_interval 60
# → ✅ poll_interval: 30 → 60

ai-mini-box config check
# → [Telegram] ✅ Connected
#   [Email]    ❌ Failed: Authentication failed
#   [LLM]      ✅ Model loaded
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `config` для управления конфигурацией.

### Требования:
1. Typer с подкомандами: `show`, `get`, `set`, `check`, `reset`
2. Используй `JsonConfigManager` из `infrastructure/config/json_config_manager.py`:
   - `load() -> AppConfig`
   - `save(config: AppConfig)`
3. AppConfig — dataclass из `core/models/config.py`:
   - `telegram: TelegramConfig` (token, allowed_chat_ids, bot_name)
   - `email: EmailConfig` (imap_server, port, login, password)
   - `llm: LlmConfig` (model_path, n_ctx, n_threads)
   - `work_schedule: WorkSchedule` (start, end)
   - `poll_interval: int`
4. `config show`: пароли по умолчанию маскировать `***`, флаг `--secrets` для показа
5. `config set`: поддержка dot-нотации (`telegram.token value`)
6. `config check`: проверка подключений (Telegram, Email, LLM-модель, БД)
7. `config reset`: сброс до значений по умолчанию
8. Сохранение через JsonConfigManager с шифрованием пароля
9. Валидация типов при set (int для poll_interval, bool для флагов)

### Структура файла:
```
tools/config.py
```

### Пример желаемого поведения:
```
$ ai-mini-box config show
telegram.token: ***
telegram.bot_name: MyShopBot
email.imap_server: imap.yandex.ru
email.login: my@email.com
llm.n_ctx: 4096
poll_interval: 30

$ ai-mini-box config set telegram.token "NEW_TOKEN"
✅ telegram.token: *** → ***

$ ai-mini-box config check
[Telegram] ✅ Bot @MyShopBot connected
[Email]    ✅ imap.yandex.ru:993 OK
[LLM]      ✅ Phi-3-mini loaded
Database:  ✅ app.db (36MB)
```
```

