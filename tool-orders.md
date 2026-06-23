# Инструмент: orders

## Описание

Управление заказами: создание, изменение статусов, история, связь с контактами и товарами. Закрывает тему "Заказ" из классификатора — оператор может быстро посмотреть все заказы клиента и их статусы.

### Команда

```bash
ai-mini-box orders COMMAND [OPTIONS]
```

### Подкоманды

| Команда | Описание |
|---------|----------|
| `list` | Список заказов |
| `show` | Детали заказа |
| `create` | Создать заказ |
| `update` | Обновить статус/данные заказа |
| `delete` | Удалить заказ |
| `search` | Поиск по заказам |

### Опции

**`orders list`:**
- `--limit N` | `--offset N` — пагинация
- `--status [new|processing|completed|cancelled]` — фильтр
- `--contact-id INT` — заказы конкретного клиента
- `--json` — JSON-вывод

**`orders create`:**
- `--contact-id INT` (обязательно)
- `--product-ids TEXT` — ID товаров через запятую
- `--total INT` — сумма в копейках
- `--notes TEXT` — примечание

**`orders update`:**
- `--id INT` (обязательно)
- `--status [new|processing|completed|cancelled]`
- `--notes TEXT`

### Примеры

```bash
ai-mini-box orders list
# → 📦 Заказ #12 | Иван Петров | 4 500₽ | processing | 2026-06-21

ai-mini-box orders create --contact-id 1 --product-ids "1,3,5" --notes "Срочно"
# → ✅ Order #13 created: 3 items, 7 200₽

ai-mini-box orders update --id 13 --status completed
# → ✅ Order #13: processing → completed
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `orders` для управления заказами.

### Требования:
1. Typer с подкомандами: `list`, `show`, `create`, `update`, `delete`, `search`
2. Используй `OrderRepo` из `ai_mini_box.core.repositories` (абстракция)
3. Реализация `SqliteOrderRepo` уже есть в `ai_mini_box.infrastructure.repositories`
4. Order — dataclass из `ai_mini_box.core.models`
5. Статусы: new → processing → completed | cancelled
6. Сумма в копейках (int), отображение в рублях
7. `--json` для машинного вывода

### Архитектура:
- Файл: `ai_mini_box/tools/orders.py`
- Регистрация: `def register(app: typer.Typer)` — `app.add_typer(orders_app, name="orders")`
- Импорты: только из `ai_mini_box.core`, `ai_mini_box.infrastructure`

### Тесты:
1. Unit: MockOrderRepo — create, list, update статуса, delete
2. Unit: валидация обязательных полей
3. Unit: фильтрация по статусу
4. Integration: CliRunner + temp БД — полный цикл (create → update → list)
5. Smoke: `--help` показывает все подкоманды

### Пример желаемого поведения:
```
$ ai-mini-box orders list
📦 #12 | Иван Петров | 4 500 ₽ | processing | 2026-06-21
📦 #13 | Анна Смирнова | 7 200 ₽ | new | 2026-06-22
```
```

### Тесты

- `test_orders.py` — 5 unit-тестов (CRUD + валидация)
- `test_orders_integration.py` — 2 интеграционных (полный цикл, фильтрация)
