# Спецификация: Web — Модуль шаблонов (REST API + React UI)

**Разработчик:** web-developer  
**Приоритет:** P1 (после реализации Части A — ML-ядра LLM-плагина)  
**Статус:** К реализации  
**Зависит от:** `27-llm-core-rewrite.md` (модели Template, TemplateStore — в LLM-плагине)

---

## 0. Цель

Создать REST API и React UI для управления 3-слойной системой шаблонов:
System (из конфига, read-only), Business (CRUD через UI), Learned (RAG, approve в UI).

---

## 1. REST API эндпоинты

**Файл:** `packages/web/ai_mini_box_web/routers/templates.py` (новый)

Router использует **lazy import** для `TemplateStore`/`Pipeline`/`ProcessingContext`
(как в существующих `routers/messages.py:42`, `routers/llm_folders.py:82`) —
импорт внутри тела функции, а не на уровне модуля, чтобы не падать при
`ImportError`, если LLM-плагин не установлен.

Все эндпоинты монтируются на `router = APIRouter(prefix="/api/v1/templates")`.

**Регистрация в server.py:**
```python
# packages/web/ai_mini_box_web/server.py
from ai_mini_box_web.routers.templates import router as templates_router
app.include_router(templates_router, prefix="/api/v1/templates", tags=["templates"])
```

### 1.1 CRUD

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/` | Список шаблонов с фильтрацией |
| `POST` | `/` | Создать бизнес-шаблон |
| `GET` | `/{template_id}` | Получить шаблон |
| `PATCH` | `/{template_id}` | Обновить шаблон (с версионированием) |
| `DELETE` | `/{template_id}` | Удалить (soft-delete, hard — с флагом) |

**Параметры фильтрации `GET /`:**
- `scope` (string: system/business/learned)
- `category` (string)
- `is_active` (bool)
- `search` (string — поиск по name и text)
- `limit` (int, default=50)
- `offset` (int, default=0)

**Pydantic-схемы:**

```python
class TemplateCreate(BaseModel):
    scope: str  # только "business" — system и learned создаются автоматически
    category: str
    name: str
    text: str
    variables: list[str] = []
    defaults: dict[str, str] = {}
    triggers: list[str] = []
    confidence_min: float = 0.6
    is_active: bool = True

    # @field_validator("scope") — only "business" allowed on create
    # system/learned scopes managed internally by TemplateStore/RAG

class TemplateUpdate(BaseModel):
    name: str | None = None
    text: str | None = None
    variables: list[str] | None = None
    defaults: dict[str, str] | None = None
    triggers: list[str] | None = None
    confidence_min: float | None = None
    is_active: bool | None = None

class TemplateResponse(BaseModel):
    id: str
    scope: str
    category: str
    name: str
    slug: str
    text: str
    variables: list[str]
    defaults: dict[str, str]
    triggers: list[str]
    confidence_min: float
    usage_count: int
    success_count: int
    success_rate: float
    version: int
    is_active: bool
    is_archived: bool
    created_at: str | None
    updated_at: str | None
```

### 1.2 Selection & Usage

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/suggest` | Умный поиск шаблонов для сообщения |
| `POST` | `/{template_id}/use` | Логирование использования шаблона |
| `POST` | `/{template_id}/approve` | Одобрить learned → business |

**`GET /suggest` — параметры:**
- `message` (string, required) — текст сообщения
- `category` (string, optional) — известная категория (если не указана, определяется через classifier)
- `limit` (int, default=5)

**Реализация (lazy import, вызов pipeline или прямых компонентов):**

```python
@router.get("/suggest")
async def suggest_templates(message: str, category: str | None = None, limit: int = 5):
    # lazy import — LLM-плагин может быть не установлен
    from ai_mini_box_llm.templates.store import TemplateStore
    from ai_mini_box_llm.extractor import EntityExtractor
    from ai_mini_box_llm.classifier import ClassifierEnsemble

    pipeline = get_service("llm")
    if pipeline:
        result = pipeline.process(message, ProcessingContext(text=message))
        category = result.category
        entities = result.entities
        confidence = result.confidence
    else:
        classifier = ClassifierEnsemble()
        classifier.load()
        extractor = EntityExtractor()
        category = category or classifier.predict(message)[0]
        entities = extractor.extract(message)
        confidence = 0.0

    store = TemplateStore(...)
    templates = store.list(
        scope="business", category=category, is_active=True, limit=limit
    )
    # сортировка: сначала те, у кого все variables в entities, потом по success_rate
    templates.sort(key=lambda t: (
        all(v in entities for v in t.variables),
        t.success_rate,
    ), reverse=True)

    return {
        "templates": templates[:limit],
        "entities": entities,
        "category": category,
        "confidence": confidence,
    }
```

**Response:**
```json
{
  "templates": [TemplateResponse, ...],
  "entities": {"name": "Иван", "order": "12345"},
  "category": "complaint",
  "confidence": 0.87
}
```

**`POST /{template_id}/use`:**
```json
{
  "message_id": "abc123",
  "operator_approved": true,
  "operator_edited": false,
  "final_text": "Приносим извинения, Иван!",
  "response_time_ms": 45
}
```

**Поля:**
- `message_id` (string) — ID сообщения в системе
- `operator_approved` (bool | null) — одобрил ли оператор этот шаблон
- `operator_edited` (bool) — редактировал ли оператор текст перед отправкой
- `final_text` (string | null) — итоговый текст ответа (с изменениями оператора)
- `response_time_ms` (int) — время ответа в мс

**`POST /{template_id}/approve`:**
- Копирует шаблон из scope=learned в scope=business
- Никакого body не требует
- Response: TemplateResponse новой business-копии

### 1.3 P2 (не входит в MVP)

Следующие эндпоинты **не реализуются в P1** (перенесены в P2):

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/stats` | Аналитика по шаблонам (chart.js на фронте) |
| `POST` | `/import` | Импорт Excel/CSV (тянет `openpyxl`) |
| `GET` | `/export` | Экспорт Excel/JSON |

Метрики для дашборда (usage_count, success_rate) доступны через `GET /` с фильтрацией.

---

## 2. React UI

### 2.1 Главная страница: Templates.tsx

**Файл:** `packages/web/frontend/src/pages/Templates.tsx` (новый)
**Роут:** `/settings/templates`

**Функции:**
- Таблица шаблонов с колонками: scope, category, name, text (truncated), usage_count, success_rate, status
- Фильтры: по scope (табы "Бизнес" / "Системные" / "Обученные"), по категории (dropdown), поиск по тексту
- Сортировка по любому столбцу
- Кнопка: "+ Новый шаблон" (открывает TemplateEditor)
- Каждая строка: клик → открыть TemplateEditor для редактирования
- Scope "system" — строки серые, кнопка редактирования скрыта
- Scope "learned" — badge "🤖 На модерации", кнопка "✅ Одобрить"
- Статистика сверху: "Всего: 47 | Активных: 32 | Используется: 18"

### 2.2 Редактор: TemplateEditor.tsx

**Файл:** `packages/web/frontend/src/components/TemplateEditor.tsx` (новый)

**React-компонент (модальное окно):**

```tsx
// Доступные переменные — жёстко зашитая константа на фронтенде
const AVAILABLE_VARIABLES = ["name", "order", "date", "address", "product", "price", "company"];

interface TemplateEditorProps {
  template: TemplateResponse | null  // null = создание нового
  variables: string[]                // = AVAILABLE_VARIABLES
  onSave: (data: TemplateCreate | TemplateUpdate) => void
  onDelete?: () => void
  onClose: () => void
}
```

**Поля формы:**
- Название (text input)
- Категория (select: заказы, вопросы, жалобы, предложения, приветствия, прощания)
- Текст шаблона (textarea с подсветкой `{{variable}}`)
- Панель вставки переменных (кнопки: `{{name}}` `{{order}}` `{{date}}` `{{address}}`)
- Предпросмотр (с подставленными тестовыми данными)
- Триггеры (tag input: "задержка" × "опоздал" × +)
- Минимальная уверенность (slider 0.0–1.0)
- Статус (toggle: активен/неактивен)

### 2.3 Виджет в чате: TemplateSelector.tsx

**Файл:** `packages/web/frontend/src/components/TemplateSelector.tsx` (новый)

**Где отображается:** на странице `MessageDetail.tsx` при ответе оператору.

**Функции:**
- После загрузки сообщения → GET `/api/v1/templates/suggest?message=...`
- Показывает 3-5 предложенных шаблонов с успешностью
- При клике на шаблон: подставляет текст в поле ответа оператора
- Нижняя кнопка "✏️ Написать свой ответ"
- После отправки ответа (если оператор выбрал шаблон) → POST `/api/v1/templates/{id}/use`
- После отправки ответа (если оператор редактировал) → `operator_edited=true`

### 2.4 Дашборд статистики: TemplateStats.tsx

**Файл:** `packages/web/frontend/src/components/TemplateStats.tsx` (новый)

**Где отображается:** страница `/settings/templates` как вкладка или секция.

**Функции:**
- График успешности по категориям (bar chart — `chart.js` + `react-chartjs-2`, уже есть в `package.json`)
- Топ-5 лучших шаблонов (таблица с трендом)
- Проблемные шаблоны (< 70% успешности)
- Селектор периода: 7д / 30д / 90д
- Кнопка экспорта CSV

---

## 3. Интеграция с существующим приложением

### 3.1 Навигация

Добавить плоский пункт меню **"Шаблоны"** → роут `/settings/templates` (аналогично `/settings/business`).

```tsx
// Layout.tsx — добавить в массив links
{ to: "/settings/templates", label: "Шаблоны" },

// App.tsx — добавить роут
<Route path="/settings/templates" element={<Templates />} />
```

### 3.2 Интеграция TemplateSelector в MessageDetail.tsx

```tsx
// MessageDetail.tsx — добавление виджета перед полем ответа
import TemplateSelector from "../components/TemplateSelector";

// Внутри компонента (после загрузки msg):
// eslint-disable-next-line react-hooks/exhaustive-deps
const suggestedTemplates = useQuery({
  queryKey: ["template-suggest", msg?.id],
  queryFn: () => fetch(`/api/v1/templates/suggest?message=${encodeURIComponent(msg.text)}`).then(r => r.json()),
  enabled: !!msg?.text,
});
```

---

## 4. Ограничения и границы ответственности

- **Не включает** авторизацию/JWT — используется существующая API-key схема
- **Не включает** роли — все операторы = admin для шаблонов
- **Не включает** сложные условия (время суток, тип клиента) — будущая версия
- **Не включает** A/B тестирование — будущая версия
- **Не трогает** существующие страницы Messages, MessageDetail (кроме вставки виджета)

---

## 6. Обновление messages.py (reprocess-chatbot)

**Файл:** `packages/web/ai_mini_box_web/routers/messages.py` (изменения)

Эндпоинт `POST /api/messages/{id}/reprocess-chatbot` переключается с `ChatbotService` на `Pipeline`.

```python
@router.post("/{item_id}/reprocess-chatbot")
def reprocess_message_chatbot(item_id: int, repos: RepoContainer = Depends(get_repos)):
    msg = repos.messages.get_by_id(item_id)
    if msg is None:
        raise HTTPException(404)

    pipeline = get_service("llm")  # Pipeline, не ChatbotService
    if pipeline is None:
        raise HTTPException(400, detail="LLM pipeline not available")

    from ai_mini_box_llm.pipeline import ProcessingContext
    result = pipeline.process(msg.text, ProcessingContext(
        history=[],
        user_name=msg.extracted_name or "",
        category=msg.category,
    ))

    msg.category = result.category
    msg.need_human = result.need_human
    msg.auto_replied = (result.reply_text is not None and not result.need_human)
    msg.auto_reply_text = result.reply_text
    msg.operator_context = f"Категория: {result.category} ({result.confidence:.0%})"
    repos.messages.update(msg)

    return {
        "success": True,
        "category": result.category,
        "reply_to_user": result.reply_text,
        "need_human": result.need_human,
        "auto_replied": msg.auto_replied,
    }
```

**Что меняется:**
- `get_service("llm")` возвращает `Pipeline` вместо `ChatbotService`
- `Pipeline.process()` вместо `chatbot_service.process_message()`
- Импорт `ProcessingContext` из `ai_mini_box_llm.pipeline`
- Удалён импорт `ChatbotService` / `ChatbotResult`

**Критерий приёмки:** `POST /api/messages/{id}/reprocess-chatbot` возвращает те же поля, что и раньше, но через новый pipeline.

**Зависимость:** Требует готового `Pipeline` из spec 27 (`27-llm-core-rewrite.md`) и запущенного `TaskScheduler` (APScheduler) — планировщик запускает sync_templates, retrain, rebuild RAG.

---

## 7. Миграция БД

Таблицы `templates`, `template_usage_log` создаются через **единый Alembic в `packages/core/migrations/`**.
`create_all()` — только для тестов.

**`env.py` — импорт LLM-моделей с fallback:**
```python
# core/migrations/env.py
from core.database import Base
from core.models import *  # noqa

try:
    from llm_plugin.models import *  # noqa
except ImportError:
    import logging
    logging.getLogger("alembic").warning(
        "llm_plugin not installed — LLM tables excluded from migration"
    )

target_metadata = Base.metadata
```

```bash
alembic revision --autogenerate -m "add_templates_module"
alembic upgrade head
```

---

## 8. Критерии приёмки

1. `GET /api/v1/templates` возвращает список с фильтрацией и пагинацией
2. `POST /api/v1/templates` создаёт шаблон, возвращает 201
3. `PATCH /api/v1/templates/{id}` обновляет шаблон, version инкрементируется
4. `DELETE /api/v1/templates/{id}` — soft-delete (is_archived=true)
5. System шаблоны нельзя удалить или изменить через API
6. `GET /api/v1/templates/suggest` возвращает топ-5 шаблонов для сообщения
7. `POST /api/v1/templates/{id}/approve` копирует learned → business
8. UI: страница Templates, редактор, дашборд и виджет в чате рендерятся без ошибок
9. Фильтры (scope, category, search) работают в списке шаблонов
10. Виджет в чате отображается на странице MessageDetail и подставляет текст в `setReplyText()`
