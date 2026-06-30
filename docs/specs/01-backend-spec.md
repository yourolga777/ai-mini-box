# ТЗ для бекенд-разработчика (web + core)

## 1. Фильтрация сообщений по contact_id

**Файлы:** `packages/web/ai_mini_box_web/routers/messages.py`

**Описание:**
- Добавить query-параметр `contact_id` на `GET /api/messages`
- Передавать в `message_repo.list(contact_id=contact_id)`

**Критерии приёмки:**
- `GET /api/messages?contact_id=5` возвращает только сообщения контакта 5
- `GET /api/messages?contact_id=999` возвращает пустой массив (не 404)

---

## 2. Эндпоинт привязки сообщения к контакту

**Файлы:** `packages/web/ai_mini_box_web/routers/messages.py`

**Описание:**
- `PUT /api/messages/{id}/contact` с телом `{ "contact_id": int }`
- Обновить `message.contact_id` и вернуть обновлённое сообщение

**Критерии приёмки:**
- Если `id` не существует — 404
- Если `contact_id` не существует — 404
- Ответ — полный объект сообщения с новым `contact_id`

---

## 3. Эндпоинты для управления папками (MessageCategory)

**Файлы:** `packages/web/ai_mini_box_web/routers/llm_folders.py`

**Описание:**
REST API для CRUD папок:

| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/llm/folders` | Список папок с количеством сообщений |
| POST | `/api/llm/folders` | Создать папку |
| PUT | `/api/llm/folders/{id}` | Обновить папку |
| DELETE | `/api/llm/folders/{id}` | Удалить папку |

Поля папки: `name` (str, unique), `description` (str, опционально), `color` (str, по умолчанию "#6b7280"), `is_system` (bool, только для чтения).

**Критерии приёмки:**
- `POST` с пустым `name` — 422
- `POST` с существующим `name` — 409
- `DELETE` системной папки (`is_system=true`) — 403
- `PUT` системной папки с изменением `name` — 403 (менять можно только `description` и `color`)
- `GET` возвращает массив объектов, каждый содержит `message_count: int`

---

## 4. АПИ-роут для выборки сообщений по папке

**Файлы:** `packages/web/ai_mini_box_web/routers/messages.py`

**Описание:**
Добавить query-параметр `category_id` на `GET /api/messages`:
- Ищет `MessageCategoryAssignment` с `category_id=...`
- Возвращает связанные сообщения
- Если категории нет — пустой массив (не 404)

---

## 5. Фикс plugin_manager._is_running()

**Файлы:** `packages/web/ai_mini_box_web/services/plugin_manager.py:187`

**Описание:**
В методе `_is_running()` проверка `proc.poll()` может вернуть `None` (процесс жив), что вызывает `TypeError` при сравнении. Нужно добавить проверку `if proc.poll() is not None`.

**Критерии приёмки:**
- `_is_running()` не падает для запущенного процесса

---

## 6. Фикс LLM plugin._ensure_tables()

**Файлы:** `packages/llm/ai_mini_box_llm/plugin.py:56`

**Описание:**
Вызов `_ensure_tables()` внутри try-блока импорта `llama-cpp-python` приводит к тому, что при отсутствии библиотеки таблицы не создаются. Вынести вызов `_ensure_tables()` перед try-блоком.

**Критерии приёмки:**
- Таблицы `llm_categories` и `llm_category_assignments` создаются даже без `llama-cpp-python`

---

## 7. Catch-all роут для SPA

**Файлы:** `packages/web/ai_mini_box_web/server.py`

**Проблема:** React Router управляет клиентскими маршрутами (`/contacts/:id`, `/messages/:id`, `/help`). При обновлении страницы (F5, Ctrl+Shift+R) браузер отправляет GET-запрос на сервер. FastAPI не находит API-роут и возвращает `{"detail":"Not Found"}`.

**Описание:**
Добавить catch-all роут, который отдаёт `index.html` для всех не-API и не-статических путей:

```python
from fastapi.responses import Response
from fastapi import HTTPException

@app.get("/{path:path}", include_in_schema=False)
async def serve_spa(path: str):
    if path.startswith("api/"):
        raise HTTPException(status_code=404)
    html_path = static_dir / "index.html"
    if html_path.exists():
        return Response(html_path.read_text(encoding="utf-8"), media_type="text/html")
    raise HTTPException(status_code=404)
```

Роут зарегистрировать **после** всех `include_router()` и после `app.mount()` для статики.

**Критерии приёмки:**
- `GET /contacts/1` — возвращает index.html, React Router управляет навигацией
- `GET /api/contacts/1` — JSON (не затронут)
- `GET /nonexistent-file.js` — 404 от StaticFiles, не index.html
- Любой не-API, не-статический путь — index.html

---

## 8. Базовая реализация plugin_catalog.py

**Файлы:** `packages/core/ai_mini_box/core/services/plugin_catalog.py`

**Описание:**
Реализация `PluginCatalog` с методами:
- `load()` — читает `data/plugin-catalog.json`
- `sync()` — мержит builtin из `ai_mini_box/data/` с кешем
- `get_status()` — возвращает список плагинов с флагами `is_installed`

**Критерии приёмки:**
- Если файл кеша не существует — читать builtin
- `sync()` не затирает кастомные записи с уникальными именами
- `get_status()` использует `importlib.metadata` для проверки установки

---

## 9. API каталога плагинов и обновлений (P2-1)

**Файлы:** `packages/web/ai_mini_box_web/routers/plugins.py`, `packages/web/ai_mini_box_web/services/plugin_manager.py`

**Описание:**

**1. Новый эндпоинт `GET /api/plugins/catalog`:**
- Использует `PluginCatalog.get_status()` из `core/services/plugin_catalog.py`
- Возвращает список всех плагинов из каталога
- Каждый элемент:
  ```json
  {
    "name": "telegram",
    "description": "Telegram bot integration...",
    "version": "1.2.0",
    "installed": true,
    "installed_version": "1.0.0",
    "has_update": true
  }
  ```

**2. Доработка `GET /api/plugins`:**
- Добавить в ответ поля: `version`, `has_update`, `description` (мержить с данными из `PluginCatalog` по `name`)
- Если плагина нет в каталоге — `description` = пустая строка, `has_update` = false

**3. Новый эндпоинт `POST /api/plugins/{name}/update`:**
- Выполняет `pip install --upgrade ai-mini-box-{name}`
- Возвращает `{ "success": bool, "output": str }`
- Аналогичен установке, но с `--upgrade`

**Критерии приёмки:**
- `GET /api/plugins/catalog` возвращает данные из `data/plugin-catalog.json` + статус установки
- `has_update=true` только если `latest_version > installed_version` (сравнение через `packaging.version`)
- `POST /api/plugins/{name}/update` возвращает успех/ошибку и лог
- Обновление недоступного плагина — 404

---

## P2-2: Auto-создание заказов из сообщений

**Файлы:**
- `packages/core/ai_mini_box/core/models.py` — `Message`: добавить `extracted_order_id`
- `packages/core/ai_mini_box/infrastructure/orm_models.py` — `MessageOrm`: добавить колонку
- `packages/core/ai_mini_box/infrastructure/mapping.py` — маппинг `extracted_order_id`
- `packages/core/ai_mini_box/infrastructure/repositories/order_repo.py` — `SqliteOrderRepo.add()` (уже есть)
- `packages/core/ai_mini_box/core/services/auto_processor.py` — логика создания заказа
- `packages/web/ai_mini_box_web/routers/messages.py` — новые эндпоинты
- `packages/web/ai_mini_box_web/routers/orders.py` — опционально

### 1. Message: новое поле `extracted_order_id`

Добавить в `Message` (core model, ORM, маппинг):
```python
extracted_order_id: Optional[int] = None
```

### 2. AutoProcessor: создание заказа

В `AutoProcessor.process()` после существующего блока `extract_entities` (который создаёт `Task`):

```python
# после Task-блока
order_info = self.llm.extract_order_info(message.text)
if order_info and order_info.get("is_order") and order_info.get("confidence", 0) >= 0.5:
    order = Order(
        contact_id=message.contact_id,
        source_message_id=message.id,
        total_kopecks=order_info.get("price_kopecks", 0),
        notes=message.text,  # исходный текст как заметка
        status="new",
    )
    created = self.order_repo.add(order)
    message.extracted_order_id = created.id
    self.message_repo.update(message)
    result.order_created = True
```

Добавить поле в `AutoProcessResult`:
```python
@dataclass
class AutoProcessResult:
    task_created: bool = False
    order_created: bool = False
    category_id: Optional[int] = None
```

### 3. Новые эндпоинты

**`GET /api/messages/{id}/order`:**
- Возвращает `Order | null` — заказ, привязанный к сообщению
- Ищет по `message.source_message_id`

**`POST /api/messages/{id}/create-order`:**
- Тело: `{ "total_kopecks": int, "notes": str }` (оба опциональны)
- Создаёт `Order` с `source_message_id = message.id`, `contact_id = message.contact_id`
- Обновляет `message.extracted_order_id`
- Возвращает `Order`
- Если заказ уже существует (extracted_order_id не null) — возвращаем 409 Conflict
- Если message.contact_id is None — 400 Bad Request (нельзя создать заказ без контакта)

### 4. Миграция БД

Новая миграция:
```sql
ALTER TABLE messages ADD COLUMN extracted_order_id INTEGER REFERENCES orders(id);
```

### Критерии приёмки:
- `AutoProcessor.process()` создаёт `Order` для сообщения, где LLM распознала заказ
- Созданный заказ имеет `source_message_id = message.id`
- `GET /api/messages/{id}/order` возвращает созданный заказ
- `POST /api/messages/{id}/create-order` создаёт заказ вручную и возвращает его
- Повторный `POST` на то же сообщение — 409 Conflict
- Создание заказа без контакта — 400 Bad Request
- Существующие тесты проходят (70/70 backend + 46 telegram)

---

## P3: Универсальный конфиг плагина

**Файлы:**
- `packages/web/ai_mini_box_web/routers/plugins.py` — новый эндпоинт
- `packages/web/ai_mini_box_web/services/plugin_manager.py` — новый метод

**Назначение:** Любой плагин (email, telegram, ...) может сохранять свой конфиг через единый API, не требуя отдельного эндпоинта. Фронтенд использует `POST /api/plugins/{name}/config`.

### 1. Новый эндпоинт `POST /api/plugins/{name}/config`

```python
@router.post("/api/plugins/{name}/config")
def set_plugin_config(
    name: str,
    config: dict,
    repos = Depends(get_repos),
):
    """
    Сохраняет конфиг плагина в data/config.json под ключом name.
    Частичное обновление: мержит переданные поля с существующими.
    """
    with open("data/config.json") as f:
        data = json.load(f)

    if name not in data:
        data[name] = {}
    data[name].update(config)

    # Атомарная запись (tmp-файл + os.replace)
    tmp = tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8")
    json.dump(data, tmp, indent=2, ensure_ascii=False)
    tmp_path = tmp.name
    tmp.close()
    os.replace(tmp_path, "data/config.json")

    return {"success": True}
```

### 2. Метод `PluginManager.save_plugin_config()`

```python
class PluginManager:
    def save_plugin_config(self, name: str, config: dict) -> None:
        """
        Сохраняет конфиг плагина.
        Эквивалент эндпоинта, вызывается из CLI при необходимости.
        """
```

### 3. Безопасность

- `name` валидируется: только латиница, цифры, дефис, подчёркивание (regex `^[a-zA-Z0-9_-]+$`)
- Если `name` невалидный — 400 Bad Request
- Файл конфига блокируется `threading.Lock` (race condition, как в `JsonConfigManager`)

### Критерии приёмки

- `POST /api/plugins/email/config { "imap_host": "imap.gmail.com" }` → `config.json["email"]["imap_host"]` = `"imap.gmail.com"`
- Частичное обновление: поля, не переданные в `config`, не теряются
- `name` с недопустимыми символами — 400
- Атомарная запись: сбой в середине не повреждает `config.json`
