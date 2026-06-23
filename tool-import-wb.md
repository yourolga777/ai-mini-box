# Инструмент: import-wb

## Описание

Импорт заказов и товаров с маркетплейсов: Wildberries, Ozon, Яндекс.Маркет. Парсит API или CSV-отчёты и создаёт заказы/товары в локальной БД.

### Команда

```bash
ai-mini-box import-wb COMMAND [OPTIONS]
```

### Подкоманды

| Команда | Описание |
|---------|----------|
| `orders` | Импорт заказов с маркетплейса |
| `products` | Импорт/обновление товаров |
| `config` | Настройка API-ключей маркетплейсов |

### Опции

**`import-wb orders`:**
- `--marketplace [wb|ozon|yam]` — маркетплейс (обязательно)
- `--from DATE` — начальная дата
- `--to DATE` — конечная дата
- `--json` — JSON-вывод

**`import-wb products`:**
- `--marketplace [wb|ozon|yam]` — маркетплейс
- `--file PATH` — CSV-файл (альтернатива API)
- `--update` — обновить существующие товары

### Примеры

```bash
ai-mini-box import-wb orders --marketplace wb --from 2026-06-01
# → ✅ Imported 15 orders from Wildberries

ai-mini-box import-wb products --file wb-products.csv
# → ✅ Imported 45 products from wb-products.csv

ai-mini-box import-wb config --marketplace wb --api-key "XXXX"
# → ✅ WB API key saved
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `import-wb` для интеграции с маркетплейсами.

### Требования:
1. Typer с подкомандами: `orders`, `products`, `config`
2. Поддержка Wildberries, Ozon, Яндекс.Маркет (через их API)
3. При импорте создаёт контакты (если нет), товары, заказы в локальной БД
4. Использует репозитории: ContactRepo, ProductRepo, OrderRepo
5. API-ключи хранятся в config.json
6. CSV-импорт как fallback (если нет API-доступа)
7. `--json` для машинного вывода

### Архитектура:
- Файл: `ai_mini_box/tools/import_wb.py`
- Регистрация: `def register(app: typer.Typer)`
- Парсеры маркетплейсов: `ai_mini_box/tools/parsers/wb.py`, `ozon.py`, `yam.py`
- Импорты: репозитории из `ai_mini_box.core`, ParseError

### Тесты:
1. Unit: MockProductRepo + MockOrderRepo — импорт из CSV
2. Unit: обработка дубликатов (обновить, не создать новый)
3. Integration: CliRunner — импорт тестового CSV
4. Smoke: --help

### Пример желаемого поведения:
```
$ ai-mini-box import-wb orders --marketplace wb --from 2026-06-01
✅ Imported 15 orders from Wildberries
✅ Created/updated 3 contacts
✅ Created/updated 22 products
```
```

### Тесты

- `test_import_wb.py` — 3 unit-теста (CSV-парсинг, дубликаты, ошибка API)
- `test_import_wb_integration.py` — 1 интеграционный
