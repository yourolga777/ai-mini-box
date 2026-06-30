# Спецификация: Каркас — Хранение бизнес-конфига для чатбота (v1)

**Разработчик:** Каркас (core)  
**Приоритет:** P0 (блокер для всех остальных)  
**Статус:** К реализации  

---

## 1. BusinessConfig — Pydantic модель

**Файл:** `packages/core/ai_mini_box/core/models.py`

Добавить новую модель `BusinessConfig`:

```python
class BusinessConfig(BaseModel):
    company_name: str = "Название компании"
    work_hours: str = "Пн-Пт 9:00-18:00"
    delivery_info: str = "Условия доставки"
    return_policy: str = "Условия возврата"
    payment_methods: str = "Способы оплаты"
    contacts: str = "Контакты"
    faq: list[dict] = Field(default_factory=list)  # [{"question": "...", "answer": "..."}]
```

## 2. Хранение в JSON

**Файл:** `packages/core/ai_mini_box/infrastructure/config.py` (или новый `business_config.py`)

- Использовать существующий `JsonConfigManager` (или его паттерн)
- Файл: `data/business_config.json`
- Методы:
  - `load_business_config() -> BusinessConfig`
  - `save_business_config(cfg: BusinessConfig)`
- Автоматическое создание с дефолтами при первом запуске (в `init` или лениво при первом чтении)

```python
# Пример структуры data/business_config.json
{
  "company_name": "Название компании",
  "work_hours": "Пн-Пт 9:00-18:00",
  "delivery_info": "...",
  "return_policy": "Возврат в течение 14 дней",
  "payment_methods": "Наличные, карта, безналичный",
  "contacts": "Телефон, email",
  "faq": [
    {"question": "Как долго доставка?", "answer": "2-5 рабочих дней"},
    {"question": "Можно ли вернуть?", "answer": "Да, в течение 14 дней"}
  ]
}
```

## 3. CLI-команда

**Файл:** `packages/core/ai_mini_box/cli.py`

Добавить `ai-mini-box business`:
- `ai-mini-box business show` — вывести текущий конфиг
- `ai-mini-box business set <key> <value>` — обновить поле
- `ai-mini-box business faq add <question> || <answer>` — добавить FAQ
- `ai-mini-box business faq remove <index>` — удалить FAQ

## 4. init-db: создавать дефолтный business_config.json

В `cli.py:init()` после создания `config.json` также создавать `data/business_config.json` с дефолтами.

## 5. Новые поля MessageModel для категорий чатбота

**Файл:** `packages/core/ai_mini_box/infrastructure/orm_models.py`

Добавить колонки в `MessageModel`:

| Колонка | SQLAlchemy тип | Назначение |
|---|---|---|
| `category` | `Mapped[str \| None]` | ЗАКАЗ / ВОПРОС / ПРЕДЛОЖЕНИЕ / ЖАЛОБА / ФЛУД |
| `subcategory` | `Mapped[str \| None]` | детализация (доставка, цена, статус...) |
| `need_human` | `Mapped[bool]` | требуется оператор |
| `auto_replied` | `Mapped[bool]` | автоответ отправлен |
| `auto_reply_text` | `Mapped[str \| None]` | текст автоответа |
| `operator_context` | `Mapped[str \| None]` | сводка для оператора |

**Файл:** `packages/core/ai_mini_box/core/models.py` (Pydantic)

Те же поля в `Message` Pydantic-модели.

**Миграция:** новая Alembic revision (зависит от `a1b2c3d4e5f6`):

```python
op.add_column("messages", sa.Column("category", sa.String(50), nullable=True))
op.add_column("messages", sa.Column("subcategory", sa.String(100), nullable=True))
op.add_column("messages", sa.Column("need_human", sa.Boolean(), server_default="0"))
op.add_column("messages", sa.Column("auto_replied", sa.Boolean(), server_default="0"))
op.add_column("messages", sa.Column("auto_reply_text", sa.Text(), nullable=True))
op.add_column("messages", sa.Column("operator_context", sa.Text(), nullable=True))
```

## Acceptance criteria

- `data/business_config.json` создаётся при `ai-mini-box init`
- `ai-mini-box business show` выводит конфиг
- `ai-mini-box business set company_name "Магазин мебели"` обновляет поле
- Чтение конфига через Python API возвращает `BusinessConfig`
- `MessageModel` содержит все 6 новых полей
- Миграция применяется без ошибок
- Старые сообщения имеют NULL в новых полях (обратная совместимость)

## Scope exclude

- Не писать ChatbotService (это задача LLM-разработчика)
- Не менять Telegram handler
- Не писать API endpoints (это задача веб-разработчика)
