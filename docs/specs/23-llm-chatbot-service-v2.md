# Спецификация: LLM — ChatbotService (v2 — финализация)

**Разработчик:** LLM-плагин  
**Приоритет:** P0  
**Статус:** К реализации  
**Зависит от:** 22-core (list_by_chat, OrderService)

---

## 1. ChatbotResult — точное объявление

**Файл:** `packages/llm/ai_mini_box_llm/chatbot_service.py`

```python
from pydantic import BaseModel

class ActionRequired(BaseModel):
    create_order: bool = False
    send_auto_reply: bool = False
    escalate_to_manager: bool = False

class ChatbotResult(BaseModel):
    category: str                              # ЗАКАЗ | ВОПРОС | ПРЕДЛОЖЕНИЕ | ЖАЛОБА | ФЛУД
    subcategory: str | None = None
    reply_to_user: str = ""
    need_human: bool = False
    operator_context: str | None = None
    action_required: ActionRequired = ActionRequired()
```

Telegram импортирует: `from ai_mini_box_llm.chatbot_service import ChatbotResult`

---

## 2. BusinessConfig — временный дублёр

Пока core не реализовал `business_config.py`:

```python
# Временная заглушка, заменить на from ai_mini_box.core.models import BusinessConfig
class BusinessConfig(BaseModel):
    company_name: str = ""
    work_hours: str = ""
    delivery_info: str = ""
    return_policy: str = ""
    payment_methods: str = ""
    contacts: str = ""
    faq: list[dict] = []
```

---

## 3. ChatbotService — архитектура

```python
class ChatbotService:
    def __init__(self, provider: BaseLLMProvider):
        self._provider = provider

    def process_message(
        self,
        text: str,
        history: list[dict],          # [{"role": "user"|"assistant", "text": "..."}]
        user_name: str,
        business_config: BusinessConfig,
    ) -> ChatbotResult:
        prompt = self._build_prompt(text, history, user_name, business_config)
        raw = self._provider.generate(prompt, max_tokens=1024, temperature=0.3)
        return self._parse_result(raw)
```

**Принципиальные решения:**
- Принимает `BaseLLMProvider` (не `LlmServiceImpl`)
- **НЕ заменяет** AutoProcessor.process()
- **НЕ трогает** extract_entities / extract_order_info
- **НЕТ** time в history (только role + text)

---

## 4. Парсинг JSON — _JSON_RE

```python
_JSON_RE = re.compile(r'\{.*?\}', re.DOTALL)

def _parse_result(self, raw: str) -> ChatbotResult:
    match = _JSON_RE.search(raw)
    if not match:
        return ChatbotResult(category="ВОПРОС", need_human=True, operator_context="Не удалось распарсить ответ ИИ")
    try:
        data = json.loads(match.group())
        return ChatbotResult(**data)
    except (json.JSONDecodeError, ValidationError):
        return ChatbotResult(category="ВОПРОС", need_human=True, operator_context="Битый JSON от ИИ")
```

---

## 5. Формат history в промпте

```python
def _format_history(self, history: list[dict]) -> str:
    if not history:
        return "(нет)"
    lines = ["Последние сообщения:"]
    for msg in history:
        prefix = "Клиент" if msg["role"] == "user" else "Вы"
        lines.append(f"{prefix}: {msg['text']}")
    return "\n".join(lines)
```

---

## 6. CHATBOT_PROMPT_TEMPLATE

**Файл:** `packages/llm/ai_mini_box_llm/prompt.py` (новый промпт, старые не трогать)

Шаблон (идентичен утверждённому в spec 18, с подстановками):
- `{text}` — сообщение
- `{history}` — отформатированная история
- `{user_name}` — имя пользователя
- `{company_name}`, `{work_hours}`, `{delivery_info}`, `{return_policy}`, `{payment_methods}`, `{contacts}` — из BusinessConfig
- `{faq}` — форматированный FAQ

---

## 7. Регистрация

**Файл:** `packages/llm/ai_mini_box_llm/plugin.py`

```python
provider = LocalProvider(config)  # или RemoteProvider
register_service("chatbot", ChatbotService(provider))
```

---

## 8. Тесты

| Файл | Что |
|---|---|
| `tests/unit/test_chatbot_service.py` | Сборка промпта, _format_history, _parse_result, fallback |
| `tests/unit/test_chatbot_result.py` | Валидация ChatbotResult |

**Не мокать provider.generate()** — использовать строку-заглушку для теста парсинга.

---

## 9. Границы ответственности

- Не менять Telegram handler
- Не менять web API
- Не менять AutoProcessor
