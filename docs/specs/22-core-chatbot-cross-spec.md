# Спецификация: Core — Cross-spec deliveries для чатбота (v1)

> **Статус: РЕАЛИЗОВАНО** (с отклонениями):
> - `list_by_chat()` не фильтрует `sent_response==True` на уровне репозитория
>   (фильтрация делается на уровне хендлера в `get_chat_history()`, что архитектурно правильнее)
> - Нет теста на `list_by_chat` в `test_message_repo.py`
> - OrderService.create_from_message() — ✅

**Разработчик:** Каркас (core)  
**Приоритет:** P0 (блокер Telegram)  
**Статус:** К реализации  
**Зависит от:** 17-core-business-config (выполнена)

---

## 1. MessageRepo.list_by_chat()

**Файл:** `packages/core/ai_mini_box/repositories/message_repo.py` (ABC)

```python
@abstractmethod
def list_by_chat(self, chat_id: str, limit: int = 5) -> list[Message]: ...
```

**Файл:** `packages/core/ai_mini_box/infrastructure/repositories.py` (SqliteMessageRepo)

```python
def list_by_chat(self, chat_id: str, limit: int = 5) -> list[Message]:
    stmt = (
        select(MessageModel)
        .where(MessageModel.chat_id == chat_id)
        .order_by(MessageModel.received_at.desc())
        .limit(limit)
    )
    return [message_from_orm(r) for r in self.session.execute(stmt).scalars()]
```

Включать только `sent_response == True` (для истории диалога нужны реально отправленные ответы).

**Тесты:** `test_message_repo.py` — 3 сообщения с одним `chat_id`, `list_by_chat` возвращает 3.

---

## 2. OrderService.create_from_message()

**Новый файл:** `packages/core/ai_mini_box/core/services/order_service.py`

```python
class OrderService:
    def __init__(self, repos: RepoContainer):
        self.repos = repos

    def create_from_message(
        self,
        message_id: int,
        contact_id: int,
        total_kopecks: int = 0,
        notes: str = "",
    ) -> Order:
        order = Order(
            contact_id=contact_id,
            total_kopecks=total_kopecks,
            notes=notes,
            status="new",
            source_message_id=message_id,
        )
        created = self.repos.orders.add(order)
        msg = self.repos.messages.get(message_id)
        if msg:
            msg.extracted_order_id = created.id
            self.repos.messages.update(msg)
        return created
```

Либо как метод `OrderRepo.create_from_message()` — на усмотрение разработчика.

---

## 3. Финализация BusinessConfig

Убедиться из spec 17:
- `BusinessConfig` Pydantic-модель в `core/models.py`
- `load_business_config()` / `save_business_config()` в `infrastructure/business_config.py`
- CLI `ai-mini-box business show/set/faq add/faq remove`
- Дефолтный `data/business_config.json` при `ai-mini-box init`

---

## 4. Границы ответственности

- Не писать ChatbotService
- Не менять Telegram handler
- Не создавать веб-эндпоинты
