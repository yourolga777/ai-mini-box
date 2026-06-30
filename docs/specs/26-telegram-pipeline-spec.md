# Спецификация: Telegram — Интеграция с новым LLM Pipeline

**Разработчик:** developer (telegram)  
**Приоритет:** P0 (после реализации Части A)  
**Статус:** К реализации  
**Зависит от:** `27-llm-core-rewrite.md` (Pipeline, ProcessingContext)

---

## 0. Цель

Заменить использование `ChatbotService` в Telegram handler на новый `Pipeline`.
Удалить legacy `_legacy_process()`. Обеспечить корректную обработку сообщений
с полями: category, need_human, auto_reply_text, operator_context.

---

## 1. Изменения в handlers.py

**Файл:** `packages/telegram/ai_mini_box_telegram/handlers.py` (изменения)

### 1.1 Заменить импорты

```python
# Было:
# from ai_mini_box_llm.chatbot_service import ChatbotResult, BusinessConfig as ChatbotBusinessConfig

# Стало:
from ai_mini_box_llm.pipeline import Pipeline, ProcessingContext
```

### 1.2 Удалить
- Функцию `_legacy_process()` (строка 43–80)
- Константу `TOPIC_MAP` (строка 10–16)
- Функцию `_load_business_config()` (строка 19–29) — бизнес-конфиг больше не нужен в handler

### 1.3 Обновить `process_update()`

```python
def process_update(
    update: dict,
    session,
    allowed_chat_ids: list[int] | None = None,
) -> bool:
    message_data = update.get("message") or update.get("business_message")
    if message_data is None:
        return False

    chat_id = message_data["chat"]["id"]
    if allowed_chat_ids and chat_id not in allowed_chat_ids:
        return False

    repos = RepoContainer(session)

    # 1. Извлекаем текст и пользователя
    text = message_data.get("text") or message_data.get("caption", "")
    from_user = message_data.get("from", {})
    first = from_user.get("first_name", "") or ""
    last = from_user.get("last_name", "") or ""
    user_name = f"{first} {last}".strip() or str(chat_id)

    # 2. Находим или создаём контакт
    contacts = repos.contacts.list(telegram=str(chat_id), limit=1)
    if contacts:
        contact = contacts[0]
    else:
        contact = repos.contacts.add(
            Contact(
                name=user_name,
                telegram=str(chat_id),
                source=MessageSource.TELEGRAM,
            )
        )

    # 3. Извлекаем телефон из текста (legacy-функция остаётся)
    extracted_phone = extract_phone(text)

    # 4. Сохраняем сообщение
    msg = repos.messages.add(
        Message(
            source=MessageSource.TELEGRAM,
            external_id=str(update.get("update_id", "")),
            chat_id=str(chat_id),
            contact_id=contact.id,
            text=text,
            extracted_phone=extracted_phone,
            extracted_name=user_name,
        )
    )

    # 5. Получаем pipeline
    pipeline = get_service("llm")
    if pipeline is None:
        logger.warning("LLM pipeline not available, skipping enrichment")
        return True

    # 6. Получаем историю диалога
    history = get_chat_history(repos, str(chat_id))

    # 7. Обрабатываем через pipeline
    try:
        result = pipeline.process(text, ProcessingContext(
            history=history,
            user_name=user_name,
            category=None,
        ))
    except Exception:
        logger.exception("Pipeline processing failed, saving message without enrichment")
        return True

    # 8. Сохраняем результат LLM-обработки
    msg.category = result.category
    msg.subcategory = None  # deprecated — не используется в новой системе
    msg.need_human = result.need_human
    msg.auto_replied = (result.reply_text is not None and not result.need_human)
    msg.auto_reply_text = result.reply_text
    msg.operator_context = f"Категория: {result.category} ({result.confidence:.0%})"
    msg.topic = _category_to_topic(result.category)  # см. п.1.4

    repos.messages.update(msg)

    # 9. Автоответ, если нужно
    if msg.auto_replied and result.reply_text:
        tg = get_service("telegram")
        if tg:
            try:
                tg.send_message(chat_id, result.reply_text)
                msg.sent_response = True
                repos.messages.update(msg)
                logger.info("Auto-reply sent to chat {}: {}", chat_id, result.reply_text[:60])
            except Exception:
                logger.exception("Failed to send auto-reply to chat {}", chat_id)

    return True
```

### 1.4 Добавить `_category_to_topic()`

```python
def _category_to_topic(category: str) -> Topic | None:
    """Маппинг категорий pipeline в legacy topic (для обратной совместимости)."""
    mapping = {
        "ЗАКАЗ": Topic.ORDER,
        "ЖАЛОБА": Topic.COMPLAINT,
        "ФЛУД": Topic.OTHER,
    }
    return mapping.get(category)

# ВАЖНО: Topic используется только для обратной совместимости
# с фильтрацией в web API. Новый pipeline не генерирует topic.
```

### 1.5 Обновить `get_chat_history()`

Функция не меняет сигнатуру, но теперь history передаётся в `ProcessingContext.history`:

```python
def get_chat_history(repos: RepoContainer, chat_id: str, limit: int = 5) -> list[dict]:
    messages = repos.messages.list_by_chat(chat_id, limit=limit)
    history = []
    for msg in reversed(messages):
        if msg.sent_response and msg.auto_reply_text:
            history.append({"role": "assistant", "text": msg.auto_reply_text})
        else:
            history.append({"role": "user", "text": msg.text})
    return history
```

---

## 2. Удалить из pyproject.toml (telegram-плагина)

Проверить, что `ai-mini-box-llm` указан как зависимость telegram-плагина.
Если есть явная зависимость от `ai_mini_box_llm.chatbot_service` или
`ai_mini_box_llm.prompt` — обновить на `ai_mini_box_llm.pipeline`.

**Файл:** `packages/telegram/pyproject.toml`

```toml
# Зависимость остаётся, но без extras
dependencies = [
    "ai-mini-box-llm>=0.2.0",     # транзитивно тянет APScheduler
    ...
]
```

**Примечание:** `apscheduler` указан в зависимостях llm-плагина (см. spec 27 §15) и транзитивно доступен telegram-плагину. Отдельно добавлять не нужно.

---

## 3. Тестирование

### 3.1 Модульные тесты

**Файл:** `packages/telegram/tests/test_handlers_pipeline.py` (новый)

| Что тестируем | Ожидание |
|---|---|
| `process_update()` с мокнутым pipeline | Сообщение сохранено, поля category/need_human заполнены |
| `process_update()` без pipeline | Сообщение сохранено, pipeline не упал |
| `process_update()` с ошибкой pipeline | Сообщение сохранено, лог ошибки, no exception |
| `_category_to_topic("ЗАКАЗ")` | Topic.ORDER |
| `_category_to_topic("ВОПРОС")` | None (no mapping) |
| `get_chat_history()` | Корректный формат для ProcessingContext |
| Автоответ: `result.auto_replied=True` | `tg.send_message()` вызван |
| Автоответ: `result.auto_replied=False` | `tg.send_message()` НЕ вызван |

### 3.2 Интеграционные тесты

- Сообщение приходит → pipeline обработка → поле `category` в БД = result.category
- Сообщение приходит → pipeline не установлен → сообщение сохранено без категории
- Сообщение приходит → pipeline падает → сообщение сохранено, лог ошибки

---

## 4. Критерии приёмки

1. `process_update()` использует `Pipeline.process()` вместо `ChatbotService.process_message()`
2. `_legacy_process()` **удалён** (код сокращается на ~50 строк)
3. `_load_business_config()` удалён — business_config не загружается в Telegram handler
4. `TOPIC_MAP` удалён — заменён на `_category_to_topic()`
5. При недоступности pipeline — сообщение сохраняется без обогащения
6. При ошибке pipeline — сообщение сохраняется, исключение логируется
7. Автоответ отправляется только если `result.auto_replied=True` и есть текст
8. Все существующие тесты telegram-плагина проходят
9. Сообщения в БД содержат `category`, `need_human`, `auto_reply_text`, `operator_context`

---

## 5. Схема вызова (sequence)

```
Telegram Webhook → process_update()
    ├── 1. Сохранение Message в БД
    ├── 2. text = message_data.text
    ├── 3. history = get_chat_history(chat_id)
    ├── 4. pipeline = get_service("llm")     # Pipeline, не ChatbotService
    ├── 5. result = pipeline.process(text, ProcessingContext(
    │       history=history,
    │       user_name=user_name,
    │       category=None,
    │   ))
    │   └── Pipeline.process():
    │       ├── cache.get(text) → hit? return cache
    │       ├── classifier.predict(text) → (category, confidence)
    │       ├── extractor.extract(text) → entities
    │       ├── retriever.retrieve(text) → RAG results
    │       ├── template_store.find_best(...) → template
    │       ├── fill_template(template, entities) → reply_text
    │       ├── cache.set(text, result)
    │       └── return PipelineResult
    ├── 6. msg.category = result.category
    ├── 7. msg.auto_reply_text = result.reply_text
    ├── 8. Если need_human=False и reply_text есть → tg.send_message()
    └── 9. return True
```
