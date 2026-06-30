# Спецификация: LLM-плагин — ChatbotService + универсальный промпт (v1)

**Разработчик:** LLM-плагин  
**Приоритет:** P0  
**Статус:** К реализации  

---

## 1. ChatbotService

**Новый файл:** `packages/llm/ai_mini_box_llm/chatbot_service.py`

```python
class ChatbotService:
    def process_message(
        self,
        text: str,
        history: list[dict],  # последние 5 сообщений: [{"role": "user"/"assistant", "text": "...", "time": "..."}]
        user_name: str,
        business_config: BusinessConfig,  # из 17-core-business-config-spec
    ) -> ChatbotResult:
        ...
```

**ChatbotResult** — Pydantic-модель:
```python
class ChatbotResult(BaseModel):
    category: str          # ЗАКАЗ | ВОПРОС | ПРЕДЛОЖЕНИЕ | ЖАЛОБА | ФЛУД
    subcategory: str | None
    reply_to_user: str
    need_human: bool
    operator_context: str | None
    action_required: ActionRequired

class ActionRequired(BaseModel):
    create_order: bool
    send_auto_reply: bool
    escalate_to_manager: bool
```

### Логика работы

1. Загружает `CHATBOT_PROMPT_TEMPLATE` (см. раздел 2)
2. Подставляет в шаблон:
   - `{company_name}`, `{work_hours}`, `{delivery_info}`, `{return_policy}`, `{payment_methods}`, `{contacts}` — из `business_config`
   - `{faq}` — форматированный список вопрос/ответ из `business_config.faq`
   - `{text}` — текущее сообщение
   - `{history}` — последние 5 сообщений
   - `{user_name}` — имя пользователя
3. Вызывает LLM с полным промптом
4. Парсит JSON-ответ
5. Валидирует по `ChatbotResult`
6. Если парсинг не удался — fallback: категория "ВОПРОС", need_human=True

### Регистрация в Service Registry

```python
# plugin.py
register_service("chatbot", ChatbotService(llm_service))
```

## 2. CHATBOT_PROMPT_TEMPLATE

**Файл:** `packages/llm/ai_mini_box_llm/prompt.py`

Добавить новый промпт:

```python
CHATBOT_PROMPT_TEMPLATE = """Ты — интеллектуальный ассистент для малого бизнеса, работающий в Telegram.
Твоя задача — обрабатывать входящие сообщения от клиентов и выполнять строго определённые действия.

==================================================
1. ТВОЯ РОЛЬ И ОГРАНИЧЕНИЯ
==================================================
- Ты — виртуальный сотрудник, который помогает бизнесу экономить время.
- Ты НЕ должен выдумывать факты. Всё, что ты не знаешь — ты пропускаешь или переводишь на оператора.
- Ты общаешься вежливо, профессионально, на русском языке.
- Ты не отвечаешь на вопросы, не относящиеся к бизнесу (флуд, спам, оскорбления). На такие сообщения отвечай: "Я не могу ответить на этот запрос. Если у вас есть вопрос по нашим товарам/услугам, я с радостью помогу."

==================================================
2. ВХОДНЫЕ ДАННЫЕ
==================================================
Текст сообщения: {text}
История диалога: {history}
Имя пользователя: {user_name}

==================================================
3. ИНФОРМАЦИЯ О КОМПАНИИ
==================================================
Компания: {company_name}
Режим работы: {work_hours}
Доставка: {delivery_info}
Возврат: {return_policy}
Оплата: {payment_methods}
Контакты: {contacts}

==================================================
4. БАЗА ЗНАНИЙ (FAQ)
==================================================
{faq}

==================================================
5. ТВОИ ЗАДАЧИ
==================================================
Определи категорию сообщения. Выбери ОДНУ из:
- ЗАКАЗ — намерение купить, заказать услугу, уточнить цену/наличие
- ВОПРОС — общий вопрос о работе компании, товарах, услугах, доставке, оплате
- ПРЕДЛОЖЕНИЕ — коммерческое предложение, предложение сотрудничества
- ЖАЛОБА — недовольство, претензия, проблема с товаром/услугой
- ФЛУД — не относится к бизнесу (спам, реклама, личные сообщения)

Если категория = ВОПРОС и есть ответ в Базе знаний — дай полный ответ.
Если категория = ЗАКАЗ — попроси уточнить детали (что, количество, город, телефон).
Если категория = ПРЕДЛОЖЕНИЕ — поблагодари, сообщи что передадите руководителю.
Если категория = ЖАЛОБА — извинись, сообщи что передадите проблему руководителю, need_human = true.
Если категория = ФЛУД — стандартный отказ.

==================================================
6. ФОРМАТ ВЫВОДА (СТРОГИЙ JSON)
==================================================
{{
  "category": "ЗАКАЗ | ВОПРОС | ПРЕДЛОЖЕНИЕ | ЖАЛОБА | ФЛУД",
  "subcategory": "уточнение (например: доставка, цена, статус заказа)",
  "reply_to_user": "текст ответа пользователю",
  "need_human": true/false,
  "operator_context": "если need_human=true, краткая сводка для оператора",
  "action_required": {{
    "create_order": false,
    "send_auto_reply": true/false,
    "escalate_to_manager": false
  }}
}}"""
```

## 3. Замена AutoProcessor

`AutoProcessor.process()` в текущем виде вызывает 4 отдельных LLM-метода (classify, extract_entities, extract_order_info, classify_category). Нужно интегрировать ChatbotService:

- `handlers.py:process_update()` (Telegram) вызывает единый `ChatbotService.process_message()` вместо цепочки
- `AutoProcessor.process_all()` для batch-обработки старых сообщений может использовать тот же `ChatbotService`
- Старые промпты (`CLASSIFY_PROMPT`, `EXTRACT_PROMPT`, `ORDER_EXTRACT_PROMPT`, `FOLDER_PROMPT`) остаются для обратной совместимости, но не используются в новом пайплайне

## 4. Интеграция с RAG

В `draft_response` RAG контекст уже подставляется. В ChatbotService он не нужен — вся база знаний передаётся в разделе 4 промпта (FAQ). RAG остаётся для генерации развёрнутых ответов на сложные вопросы.

## Acceptance criteria

- `ChatbotService.process_message()` возвращает валидный `ChatbotResult`
- Промпт заполняется бизнес-данными из `BusinessConfig`
- Если business_config пустой — промпт работает с дефолтными значениями
- Парсинг JSON из LLM — стабильный (fallback при ошибке парсинга)
- `ChatbotService` зарегистрирован в `Service Registry` как `"chatbot"`
- Старые тесты `test_auto_processor.py` проходят (или обновлены)

## Scope exclude

- Не менять Telegram handler (это задача Telegram-разработчика)
- Не писать веб-API
- Не менять каркас (BusinessConfig уже сделан в 17-core)
