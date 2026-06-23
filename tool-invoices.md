# Инструмент: invoices

## Описание

Создание счетов и чеков в PDF, отправка клиенту на Email/Telegram/WhatsApp. Полезно для микробизнеса, который выставляет счета вручную.

### Команда

```bash
ai-mini-box invoices COMMAND [OPTIONS]
```

### Подкоманды

| Команда | Описание |
|---------|----------|
| `create` | Создать счёт для заказа |
| `list` | Список счетов |
| `send` | Отправить счёт клиенту |
| `template` | Управление шаблонами PDF |

### Опции

**`invoices create`:**
- `--order-id INT` (обязательно) — ID заказа
- `--output PATH` — путь для PDF (default: data/invoices/)
- `--template TEXT` — имя шаблона (default: default)

**`invoices send`:**
- `--invoice-id INT` (обязательно)
- `--channel [email|telegram|whatsapp]` — канал отправки

### Примеры

```bash
ai-mini-box invoices create --order-id 12
# → ✅ Invoice #1 created: data/invoices/invoice-1.pdf (всего: 4 500₽)

ai-mini-box invoices send --invoice-id 1 --channel email
# → ✅ Invoice #1 sent to ivan@mail.ru

ai-mini-box invoices list
# → 🧾 #1 | Заказ #12 | 4 500₽ | created | 2026-06-21
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `invoices` для создания и отправки счетов.

### Требования:
1. Typer с подкомандами: `create`, `list`, `send`, `template`
2. Генерация PDF через reportlab (зависимость: reportlab)
3. Данные берутся из OrderRepo и ProductRepo
4. Шаблоны: HTML + CSS → конвертация в PDF (или reportlab напрямую)
5. Отправка через существующие каналы (EmailChannel, TelegramChannel)
6. Сохранение счетов в БД (InvoiceRepo — создать)

### Архитектура:
- Файл: `ai_mini_box/tools/invoices.py`
- Регистрация: `def register(app: typer.Typer)`
- Новые модели: `Invoice` в `ai_mini_box.core.models`
- Новый репозиторий: `InvoiceRepo` в `ai_mini_box.core.repositories`

### Тесты:
1. Unit: MockInvoiceRepo — create, list
2. Unit: генерация PDF в tmp_path
3. Integration: CliRunner — полный цикл (create → list → send)
4. Smoke: --help

### Пример желаемого поведения:
```
$ ai-mini-box invoices create --order-id 12
✅ Invoice #1: data/invoices/invoice-1.pdf (4 500 ₽)
```
```

### Тесты

- `test_invoices.py` — 3 unit-теста
- `test_invoices_integration.py` — 1 интеграционный
