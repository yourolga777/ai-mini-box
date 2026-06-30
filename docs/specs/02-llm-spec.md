# ТЗ для разработчика LLM-плагина

> **Примечание:** Раздел 5 (`keyword_folder_assign`) — НЕ РЕАЛИЗОВАН.
> ChatbotService заменил keyword-based классификацию на LLM-классификацию.
> Спецификация оставлена для истории, код не требуется.

## 1. Модели MessageCategory и MessageCategoryAssignment

**Файлы:** `packages/llm/ai_mini_box_llm/models.py` (новый)

**Описание:**
SQLAlchemy ORM модели для хранения папок (категорий) сообщений:

```python
class MessageCategory(Base):
    __tablename__ = "llm_categories"
    id: int (PK, autoincrement)
    name: str (unique, not null)           # название папки
    description: str | None                # описание
    color: str (default="#6b7280")         # цвет для UI
    is_system: bool (default=False)        # системная (нельзя удалить)
    order: int (default=0)                 # порядок сортировки
    created_at: datetime
    assignments: relationship -> MessageCategoryAssignment

class MessageCategoryAssignment(Base):
    __tablename__ = "llm_category_assignments"
    id: int (PK, autoincrement)
    message_id: int (FK -> messages.id, not null)
    category_id: int (FK -> llm_categories.id, not null)
    assigned_by: str (default="manual")    # "manual" | "keyword" | "llm"
    created_at: datetime
```

**Критерии приёмки:**
- `name` уникален
- При удалении категории удаляются и assignment (cascade)
- При удалении сообщения — assignment удаляется (cascade)
- Unique constraint на пару `(message_id, category_id)` — одно сообщение может быть в папке только один раз

---

## 2. KeywordClassifier (уровень 1)

**Файлы:** `packages/llm/ai_mini_box_llm/models.py` — уже есть `classify_category_keyword(text, categories)`

**Описание:**
Функция классификации по ключевым словам:
- Сравнивает `text` с `category.name` (по полному совпадению и по вхождению)
- Если ни одна категория не подошла — возвращает категорию "Другое" (если есть)
- Если "Другое" нет — возвращает первую категорию

**Критерии приёмки:**
- "курьер" → категория "Курьер"
- "доставка опаздывает" → категория "Доставка"
- "привет" → "Другое" (если нет совпадений)

---

## 3. AutoProcessor._assign_llm_folder() (уровень 2)

**Файлы:** `packages/llm/ai_mini_box_llm/auto_processor.py`

**Описание:**
Метод `_assign_llm_folder()` в `AutoProcessor`:
- Проверяет, установлен ли LLM-сервис
- Загружает все категории из БД через raw SQL
- Вызывает `llm.classify_category(text, categories)` из провайдера
- Создаёт `MessageCategoryAssignment` с `assigned_by="llm"`, если ещё не назначено
- Оборачивать в try/except — никакое исключение не должно ломать основной поток

**Критерии приёмки:**
- Если LLM-сервис недоступен — возвращает False без ошибки
- Если категорий нет — возвращает False
- Если классификация вернула None — пропускает
- Если связь уже существует — пропускает (idempotent)

---

## 4. AutoProcessor.process_all() (батч)

**Файлы:** `packages/llm/ai_mini_box_llm/auto_processor.py`

**Описание:**
Метод `process_all(limit=50)`:
- Загружает `limit` сообщений без ассоциаций (проверить, что `MessageCategoryAssignment` для `message_id` нет)
- Для каждого вызывает `self.process(msg, contact)`
- Возвращает количество обработанных сообщений

**Критерии приёмки:**
- Не обрабатывает сообщения без `text`
- Пропускает уже назначенные сообщения
- Не падает на первом же сообщении при ошибке

---

## 5. Интеграция: вызов keyword_folder_assign() после получения сообщения

**Файлы:** `packages/telegram/ai_mini_box_telegram/handlers.py`

**Описание:**
После сохранения сообщения и вызова `auto_processor.process()`, вызвать `keyword_folder_assign(session, msg, text, topic)`:
- Загружает все `MessageCategory` через session
- Сравнивает `topic.value.lower()` с `category.name.lower()`
- При совпадении создаёт `MessageCategoryAssignment` с `assigned_by="keyword"`
- Обрабатывать исключения — не ломать обработку сообщения

**Критерии приёмки:**
- Если `topic` совпадает с именем категории — сообщение привязывается
- Если совпадений нет — сообщение остаётся без папки
- Повторная привязка того же сообщения к той же папке — idempotent

---

## 6. _ensure_tables() вне try-блока

**Файлы:** `packages/llm/ai_mini_box_llm/plugin.py:56`

**Описание:**
Перенести вызов `self._ensure_tables()` перед блоком `try: import llama_cpp`. Таблицы `llm_categories` должны создаваться независимо от наличия `llama-cpp-python`.

**Критерии приёмки:**
- Таблицы создаются при старте плагина, даже если `llama-cpp-python` не установлен
- Если БД не инициализирована — graceful degradation (лог, без падения)

---

## P2-2: extract_order_info

**Файлы:**
- `packages/llm/ai_mini_box_llm/providers/base.py` — добавить абстрактный метод
- `packages/llm/ai_mini_box_llm/providers/local.py` — реализация
- `packages/llm/ai_mini_box_llm/providers/remote.py` — реализация
- `packages/llm/ai_mini_box_llm/service.py` — метод `extract_order_info()` в `LlmServiceImpl`
- `packages/llm/ai_mini_box_llm/prompt.py` — новый промпт (опционально, если не встроен в метод)

**Описание:**

Требуется новый метод `extract_order_info(text: str) -> Optional[dict]]` для определения, является ли сообщение заказом, и извлечения деталей.

**Метод `BaseLLMProvider.extract_order_info(text) -> Optional[dict]`:**
- Принимает текст сообщения
- Возвращает `None`, если сообщение не является заказом
- Возвращает словарь вида:
  ```python
  {
    "is_order": True,
    "product": "Ноутбук Lenovo ThinkPad",
    "quantity": 2,
    "price_kopecks": 15000000,  # 150 000.00 руб
    "confidence": 0.87  # 0.0–1.0
  }
  ```

**Реализация через LLM-промпт:**
- Промпт просит LLM определить, является ли сообщение заказом товара/услуги
- Извлекает: название товара (или услуги), количество, цену
- Если уверенность < 0.5 → возвращаем `None`
- Формат ответа — JSON (строгий, без лишнего текста)
- Промпт должен обрабатывать русский язык и разговорный стиль (мессенджеры)

**Примеры сообщений-заказов:**
- «Мне нужно 2 ноутбука Lenovo»
- «Хочу заказать пиццу Маргариту»
- «Сколько стоит доставка? Хочу заказать»
- «Пришлите 5 коробок бумаги А4»

**Примеры НЕ-заказов:**
- «Здравствуйте, у меня вопрос»
- «Когда приедет курьер?»
- «У вас есть в наличии?» (вопрос, а не заказ)
- «Спасибо, всё отлично»

**Критерии приёмки:**
- `extract_order_info("Мне нужно 2 ноутбука")` → `{ "is_order": True, "product": "ноутбук", "quantity": 2, ... }`
- `extract_order_info("Сколько стоит доставка?")` → `{ "is_order": False, ... }` или `None`
- Промпт работает на русском языке
- Допускается false-negative, но false-positive только при `confidence >= 0.7`
- Метод не падает при пустом тексте — возвращает `None`
- Если LLM вернула непарсируемый ответ — возвращаем `None` (graceful degradation)
