# Спецификация: Telegram-плагин — Интеграция ChatbotService (v2)

> **Статус: РЕАЛИЗОВАНО**
> Отклонение: `send_reply()` в спецификации, в коде — `send_message()`.
> Функционально идентично.

**Разработчик:** Telegram-плагин  
**Приоритет:** P0  
**Статус:** К реализации  
**Зависит от:** 22-core, 23-llm

---

## Зависимости от других spec

| Зависимость | От кого | Spec | Статус |
|---|---|---|---|
| `BusinessConfig` + `load_business_config()` | Core | 17 + 22 | К реализации |
| `ChatbotService` + `ChatbotResult` | LLM | 23 | К реализации |
| `MessageRepo.list_by_chat()` | Core | 22 | К реализации |
| `OrderService.create_from_message()` | Core | 22 | К реализации |
| Новые поля MessageModel + миграция | Core | 17 | К реализации |
| `send_reply()` метод TelegramService | Сам Telegram | 19 | Этот таск |

## Решения из Q&A (закреплённые)

- `ChatbotResult` импортировать из `ai_mini_box_llm.chatbot_service`
- `load_business_config()` — временная заглушка в Telegram если core не готов
- `list_by_chat(chat_id, limit)` — уже есть в core после spec 22
- `create_order` — через `OrderService.create_from_message()`, **не через HTTP**
- `_legacy_process` — **упрощённый** (только save, без classify/AutoProcessor)
- `topic` остаётся null, `category` — строка. Опциональный маппинг `category → Topic`
- `history` — **без time**, только role + text
- `send_reply` — метод на `TelegramService`, вызывается через `get_service("telegram")`

---

## 1. Изменение process_update()

**Файл:** `packages/telegram/ai_mini_box_telegram/handlers.py`

Текущая `process_update()` вызывает цепочку:
1. Классификация топика (LLM → keyword)
2. Извлечение телефона
3. Извлечение имени
4. Генерация draft_response
5. Сохранение Message
6. keyword_folder_assign
7. AutoProcessor.process()

**Новая `process_update()`:**

```
1. Сохранить Message (сразу, чтобы был ID)
2. Получить последние 5 сообщений из этого чата (из БД)
3. Загрузить BusinessConfig
4. Вызвать ChatbotService.process_message(text, history, user_name, business_config)
5. Сохранить результат на Message:
   - message.category = result.category
   - message.subcategory = result.subcategory
   - message.need_human = result.need_human
   - message.auto_replied = result.action_required.send_auto_reply
   - message.auto_reply_text = result.reply_to_user
   - message.operator_context = result.operator_context
6. Если result.action_required.send_auto_reply = True:
   - Отправить result.reply_to_user через bot.send_message(chat_id, text)
   - Обновить message.sent_response = True
7. Если result.need_human = True:
   - Флаг на сообщении уже стоит
   - (опционально) отправить уведомление оператору
8. Если result.action_required.create_order = True:
   - Вызвать OrderService.create_from_message(message_id=msg.id, contact_id=contact.id)
```

### История диалога

```python
def get_chat_history(chat_id: str, limit: int = 5) -> list[dict]:
    """Последние limit сообщений из чата."""
    messages = repos.messages.list_by_chat(chat_id, limit=limit)
    history = []
    for msg in reversed(messages):  # от старых к новым
        role = "assistant" if msg.sent_response and msg.auto_reply_text else "user"
        text = msg.auto_reply_text if role == "assistant" else msg.text
        history.append({"role": role, "text": text})
    return history
```

## 2. Загрузка BusinessConfig

**Временная заглушка** (если core не готов):

```python
from ai_mini_box_llm.chatbot_service import BusinessConfig

def _load_business_config() -> BusinessConfig:
    path = Path("data/business_config.json")
    if path.exists():
        return BusinessConfig(**json.loads(path.read_text()))
    return BusinessConfig()
```

Когда core готов — заменить на:
```python
from ai_mini_box.core.models import BusinessConfig
from ai_mini_box.infrastructure.business_config import load_business_config
```

## 3. Получение ChatbotService

```python
chatbot = get_service("chatbot")
if chatbot is None:
    _legacy_process(update, session)
    return
result = chatbot.process_message(text, history, user_name, business_config)
```

## 4. Отправка ответа

Через `TelegramService.send_reply()`:

```python
tg = get_service("telegram")
if tg and result.action_required.send_auto_reply:
    sent = tg.send_reply(chat_id, result.reply_to_user)
    if sent:
        msg.sent_response = True
        repos.messages.update(msg)
```

**Реализация в bot.py:**
```python
class TelegramService:
    def send_reply(self, chat_id: str, text: str) -> bool:
        try:
            self.bot.send_message(chat_id=chat_id, text=text)
            return True
        except Exception:
            logger.exception("Failed to send auto-reply to chat %s", chat_id)
            return False
```

## 5. Fallback _legacy_process

Упрощённый — только сохранить сообщение, никакой классификации:

```python
def _legacy_process(update, session):
    """Fallback при отсутствии ChatbotService — только save + extract."""
    message_data = _extract_message_data(update)
    contact = _get_or_create_contact(session, message_data)
    text = message_data.get("text", "")
    phone = _extract_phone(text)
    name = message_data.get("from_name", "")
    msg = Message(
        text=text, source=MessageSource.TELEGRAM,
        extracted_phone=phone, extracted_name=name,
        chat_id=str(message_data.get("chat_id", "")),
        external_id=str(message_data.get("message_id", "")),
    )
    repos.messages.add(msg)
```

## 6. Опциональный маппинг category → Topic

```python
TOPIC_MAP = {
    "ЗАКАЗ": Topic.ORDER,
    "ЖАЛОБА": Topic.COMPLAINT,
    "ВОПРОС": Topic.OTHER,
    "ПРЕДЛОЖЕНИЕ": Topic.OTHER,
    "ФЛУД": Topic.OTHER,
}
msg.topic = TOPIC_MAP.get(result.category)
```

## Acceptance criteria

- Новое сообщение из Telegram → `ChatbotService.process_message()` вызван
- Если `send_auto_reply=True` → ответ отправлен в Telegram через `bot.send_message()`
- Все поля (category, subcategory, need_human, auto_replied, auto_reply_text, operator_context) сохранены на Message
- История последних 5 сообщений корректно собирается (без time)
- `create_order=True` → вызван `OrderService.create_from_message()`, не HTTP
- Если ChatbotService не зарегистрирован → `_legacy_process()` (только save, без потери сообщения)
- `keyword_folder_assign()` не вызывается
- `topic` опционально заполняется из `category` через `TOPIC_MAP`

## Scope exclude

- Не писать ChatbotService (это LLM-разработчик)
- Не менять Pydantic/SQLAlchemy модели (это каркас)
- Не писать API эндпоинты
- Не реализовывать web-уведомления оператора (только флаг need_human)
