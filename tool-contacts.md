# Инструмент: contacts

## Описание

Управление контактами: CRUD + поиск + импорт/экспорт.

### Команда

```bash
ai-mini-box contacts COMMAND [OPTIONS]
```

### Подкоманды

| Команда | Описание |
|---------|----------|
| `list` | Список контактов |
| `show` | Детальная информация о контакте |
| `add` | Добавить контакт |
| `update` | Обновить контакт |
| `delete` | Удалить контакт |
| `search` | Поиск контактов |
| `import` | Импорт из CSV/JSON |
| `export` | Экспорт в CSV/JSON |

### Опции для подкоманд

**`contacts list`:**
- `--limit N` | `--offset N` — пагинация
- `--sort [name|email|spent|date]` — сортировка
- `--json` — JSON-вывод

**`contacts add`:**
- `--name TEXT` (обязательно)
- `--phone TEXT` | `--email TEXT`
- `--telegram TEXT` — Telegram username

**`contacts import`:**
- `--file PATH` (обязательно) — CSV или JSON
- `--format [csv|json]`

**`contacts export`:**
- `--output PATH` (обязательно)
- `--format [csv|json]`

### Примеры

```bash
ai-mini-box contacts list
# → 👤 Иван Петров | ivan@mail.ru | Потрачено: 15 000₽
#   👤 Анна Смирнова | anna@yandex.ru | Потрачено: 7 500₽

ai-mini-box contacts add --name "Олег" --phone "+7-999-123-45-67"
# → ✅ Contact added: Олег (id: 42)

ai-mini-box contacts search "иван"
# → 👤 Иван Петров | ivan@mail.ru

ai-mini-box contacts export --output contacts.csv --format csv
# → ✅ Exported 34 contacts to contacts.csv
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `contacts` для управления контактами.

### Требования:
1. Typer с подкомандами: `list`, `show`, `add`, `update`, `delete`, `search`, `import`, `export`
2. Используй `SqliteContactRepo` из `infrastructure/database/repositories/contact_repo.py`:
   - `list(limit, offset, sort) -> list[Contact]`
   - `get_by_id(id) -> Contact`
   - `upsert(contact) -> Contact`
   - `delete(id) -> bool`
   - `search(query) -> list[Contact]`
3. Contact — dataclass из `core/models/contact.py`
4. Импорт CSV: первая строка — заголовки (name, phone, email, telegram)
5. Импорт JSON: массив объектов с теми же полями
6. Экспорт: запись в CSV или JSON
7. `--json` для машинного вывода
8. Валидация: при add/update проверять обязательные поля

### Структура файла:
```
tools/contacts.py
```

### Пример желаемого поведения:
```
$ ai-mini-box contacts list
👤 Иван Петров | ivan@mail.ru | Потрачено: 15 000 ₽
👤 Анна Смирнова | anna@yandex.ru | Потрачено: 7 500 ₽

$ ai-mini-box contacts add --name "Олег" --phone "+7-999-123-45-67"
✅ Contact added: Олег (id: 42)

$ ai-mini-box contacts delete 42
✅ Contact deleted
```
```

