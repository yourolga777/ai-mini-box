# ТЗ для Telegram-разработчика

> **Статус: ЗАКРЫТ** — Раздел 1 (`keyword_folder_assign`) не реализован.
> Заменён ChatbotService в spec 19-telegram-chatbot-integration-spec.
> Остальные разделы (конфиг, FileTelegramStateRepo) реализованы.

## 1. Keyword-based folder assignment

**Файлы:** `packages/telegram/ai_mini_box_telegram/handlers.py`

**Описание:**
Функция `keyword_folder_assign(session, msg, text, topic)`, вызываемая после сохранения сообщения:
- Импортирует `MessageCategory` и `MessageCategoryAssignment` из `ai_mini_box_llm.models`
- Если LLM-плагин не установлен — возвращает без ошибки (ImportError → return)
- Загружает все `MessageCategory` через `session.execute(select(MessageCategory))`
- Сравнивает `topic.value.lower()` с `category.name.lower()`
- При совпадении создаёт `MessageCategoryAssignment` с `assigned_by="keyword"`
- Если связь уже существует — пропускает (проверить через select перед insert)
- Ошибки логировать через `logger.exception()`, не пробрасывать наверх

**Критерии приёмки:**
- Если `topic = "Курьер"` и есть категория "Курьер" → assignment создаётся
- Если топик не совпадает ни с одной категорией → ничего не происходит
- Повторный вызов с тем же `(msg.id, cat.id)` — второй раз не создаёт дубль
- Если `ai_mini_box_llm` не установлен — без ошибки
- Если таблицы `llm_categories` не существует — без ошибки

---

## 2. Собственный конфиг Telegram-плагина

**Файлы:** `packages/telegram/ai_mini_box_telegram/bot.py`, `commands.py`, новый `config.py`

**Описание:**
- Создать отдельный JSON-конфиг `data/telegram_config.json` (рядом с `telegram_offset.json`)
- Структура:
  - `api_base_url` (str, default `"https://api.telegram.org/bot"`)
  - `request_timeout` (int, default `10`)
  - `poll_interval` (int, default `2` секунды)
- Токен читать из core AppConfig (`telegram_token`) — уже есть, менять не нужно
- `allowed_chat_ids` — из core AppConfig — уже есть
- CLI-команда `ai-mini-box telegram config show/set` для просмотра и изменения
- Если файла `telegram_config.json` нет — создать при первом запуске с дефолтами

**Критерии приёмки:**
- `bot.py` читает BASE URL из `data/telegram_config.json`, не хардкодит
- `commands.py` читает `poll_interval` из `data/telegram_config.json`
- `telegram_token` по-прежнему из core AppConfig (sensitive field)
- `allowed_chat_ids` по-прежнему из core AppConfig
- Если файла нет — создаётся при первой команде с default-значениями
- CLI `show` отображает текущие значения (токен маскировать)
- CLI `set <key> <value>` обновляет поле и сохраняет

---

## 3. Состояние бота (offset)

**Файлы:** `packages/telegram/ai_mini_box_telegram/state.py`

**Описание:**
Реализовать `FileTelegramStateRepo` — сохранение `offset` в файл `data/telegram_offset.json`.
- Атомарная запись: запись во временный файл → rename
- Чтение при старте: если файла нет → offset = None
- Обработка битого JSON → offset = None

**Критерии приёмки:**
- После первого `save_offset(42)`, при повторном запуске `get_offset() == 42`
- При повреждённом файле — возвращается None, новое значение сохранится
- rename гарантирует атомарность (не будет половинчатой записи)
