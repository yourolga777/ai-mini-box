# Инструмент: products

## Описание

Управление товарами: CRUD + поиск + импорт/экспорт. Товары используются как контекст при генерации черновиков ответов.

Цены хранятся в **копейках** (int) для избежания floating-point ошибок.

### Команда

```bash
ai-mini-box products COMMAND [OPTIONS]
```

### Подкоманды

| Команда | Описание |
|---------|----------|
| `list` | Список товаров |
| `show` | Информация о товаре |
| `add` | Добавить товар |
| `update` | Обновить товар |
| `delete` | Удалить товар |
| `search` | Поиск товаров |
| `import` | Импорт из CSV/JSON |
| `export` | Экспорт в CSV/JSON |

### Опции для подкоманд

**`products add`:**
- `--name TEXT` (обязательно) — название товара
- `--price INT` — цена в копейках (обязательно)
- `--stock INT` — остаток на складе (default: 0)
- `--description TEXT` — описание

**`products import`:**
- `--file PATH` (обязательно)
- `--format [csv|json]`

**`products list`:**
- `--limit N` | `--offset N`
- `--sort [name|price|stock]`
- `--json`

### Примеры

```bash
ai-mini-box products list
# → 📦 Футболка белая | 1 999₽ | 50 шт.
#   📦 Джинсы синие | 4 500₽ | 20 шт.

ai-mini-box products add --name "Кружка" --price 79900 --stock 100
# → ✅ Product added: Кружка (id: 15), цена: 799₽

ai-mini-box products import --file products.csv --format csv
# → ✅ Imported 15 products from products.csv
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `products` для управления товарами.

### Требования:
1. Typer с подкомандами: `list`, `show`, `add`, `update`, `delete`, `search`, `import`, `export`
2. Используй `SqliteProductRepo` из `infrastructure/database/repositories/product_repo.py`:
   - `list(limit, offset, sort) -> list[Product]`
   - `get_by_id(id) -> Product`
   - `upsert(product) -> Product`
   - `delete(id) -> bool`
   - `search(query) -> list[Product]`
3. Product — dataclass из `core/models/product.py`
4. **Цена в копейках**: ввод в рублях (через `--price`), хранение в int, отображение в рублях
5. Импорт: CSV (name, price_kopecks, stock, description) и JSON
6. `--json` для машинного вывода
7. При list отображать цену как "1 999₽"

### Архитектура:
- Файл: `ai_mini_box/tools/products.py`
- Регистрация: `def register(app: typer.Typer)` — `app.add_typer(products_app, name="products")`
- Использует `ProductRepo` из `ai_mini_box.core.repositories` (абстракция)
- Реализация `SqliteProductRepo` — из `ai_mini_box.infrastructure.repositories`
- Product — dataclass из `ai_mini_box.core.models`

### Тесты:
1. Unit: MockProductRepo — add, list, update, delete, search
2. Unit: цена в копейках, отображение в рублях
3. Unit: импорт CSV и JSON
4. Integration: CliRunner — полный CRUD-цикл
5. Smoke: --help показывает все подкоманды

### Структура файла:
```
tools/products.py
```

### Пример желаемого поведения:
```
$ ai-mini-box products list
📦 Футболка белая    | 1 999 ₽ | 50 шт.
📦 Джинсы синие      | 4 500 ₽ | 20 шт.
📦 Кружка "Hello"    | 799 ₽   | 100 шт.

$ ai-mini-box products add --name "Кепка" --price 149900 --stock 200
✅ Product added: Кепка (id: 16)

$ ai-mini-box products search "фут"
📦 Футболка белая | 1 999 ₽
📦 Футболка чёрная | 2 499 ₽
```
```

