# Инструмент: search

## Описание

Полнотекстовый поиск по истории сообщений, контактам и товарам.

Использует SQLite ILIKE для поиска. Поддерживает сортировку по дате, фильтрацию по теме, пагинацию.

### Команда

```bash
ai-mini-box search COMMAND [OPTIONS] QUERY
```

### Подкоманды

| Команда | Описание |
|---------|----------|
| `messages` | Поиск по сообщениям |
| `contacts` | Поиск по контактам |
| `products` | Поиск по товарам |

### Аргументы

| Аргумент | Тип | Описание |
|----------|-----|----------|
| `QUERY` | STRING | Поисковый запрос |

### Опции

**`search messages`:**
- `--topic [Цены|Заказ|Жалоба|График|Другое]` — фильтр по теме
- `--limit N` — максимум результатов (default: 20)
- `--offset N` — смещение для пагинации
- `--json` — вывод в JSON
- `--from DATE` — начальная дата (YYYY-MM-DD)
- `--to DATE` — конечная дата

**`search contacts`:**
- `--limit N` — максимум результатов
- `--json` — вывод в JSON

**`search products`:**
- `--min-price INT` — минимальная цена (в копейках)
- `--max-price INT` — максимальная цена
- `--limit N` — максимум результатов
- `--json` — вывод в JSON

### Примеры

```bash
ai-mini-box search messages "доставка"
# → 📧 [2026-06-20] @ivan: "Сколько стоит доставка?" → Цены

ai-mini-box search messages --topic Жалоба --limit 5 "товар"
# → 📧 [2026-06-19] @petr: "Товар пришёл сломанным" → Жалоба

ai-mini-box search contacts "Иван"
# → 👤 Иван Петров | ivan@mail.ru | spent: 15,000₽

ai-mini-box search products --json "футболка"
# → [{"id": 1, "name": "Футболка белая", "price": 199900, "stock": 50}]
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `search` для полнотекстового поиска по сообщениям, контактам и товарам.

### Требования:
1. Typer с подкомандами: `messages`, `contacts`, `products`
2. Используй существующий `SearchService` из `core/services/search_service.py`:
   - Методы: `search_messages(query, topic, limit, offset, from_date, to_date)`
   - Методы: `search_contacts(query, limit)`
   - Методы: `search_products(query, min_price, max_price, limit)`
3. Каждый метод возвращает список dataclass'ов или ORM-объектов
4. Флаг `--json` выводит результат как JSON-массив
5. Человеко-читаемый вывод по умолчанию (с эмодзи для типа)
6. Пагинация: `--limit` (default 20) и `--offset`
7. Для `messages`: цветной вывод по темам (Цены=🟢, Жалоба=🔴, Заказ=🔵, График=🟡, Другое=⚪)
8. Валидация параметров: --topic принимает только 5 значений

### Архитектура:
- Файл: `ai_mini_box/tools/search.py`
- Регистрация: `def register(app: typer.Typer)` — `app.add_typer(search_app, name="search")`
- Использует `ContactRepo`, `ProductRepo`, `MessageRepo` из `ai_mini_box.core.repositories`
- Все репозитории — read-only (list, search)
- Вывод: цветной (цвета по темам), с эмодзи

### Тесты:
1. Unit: MockContactRepo + MockProductRepo + MockMessageRepo — поиск по всем типам
2. Unit: фильтрация по теме сообщений
3. Unit: пагинация (limit + offset)
4. Integration: CliRunner — поиск в tmp БД
5. Smoke: --help показывает подкоманды messages/contacts/products

### Структура файла:
```
tools/search.py
```

### Пример желаемого поведения:
```
$ ai-mini-box search messages "доставка"
📧 1. [2026-06-20] @ivan → Цены: "Сколько стоит доставка?"
📧 2. [2026-06-19] @petr → График: "Во сколько доставка?"

$ ai-mini-box search contacts "ан"
👤 Иван Петров | ivan@mail.ru | Потрачено: 15 000 ₽
👤 Анна Смирнова | anna@yandex.ru | Потрачено: 7 500 ₽

$ ai-mini-box search products --json "фут"
[{"id":1,"name":"Футболка белая","price":199900,"stock":50}]
```
```

