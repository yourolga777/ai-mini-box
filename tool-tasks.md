# Инструмент: tasks

## Описание

Внутренние задачи и напоминания: дедлайны, follow-up с клиентами, передача задач между сотрудниками. Лёгкий таск-трекер прямо в CLI.

### Команда

```bash
ai-mini-box tasks COMMAND [OPTIONS]
```

### Подкоманды

| Команда | Описание |
|---------|----------|
| `list` | Список задач |
| `add` | Добавить задачу |
| `done` | Отметить выполненной |
| `delete` | Удалить задачу |
| `remind` | Настроить напоминание |

### Опции

**`tasks list`:**
- `--status [pending|done]` — фильтр
- `--priority [low|medium|high]` — фильтр
- `--limit N` — пагинация
- `--json` — JSON-вывод

**`tasks add`:**
- `--title TEXT` (обязательно)
- `--description TEXT`
- `--priority [low|medium|high]` (default: medium)
- `--deadline TEXT` — дата (YYYY-MM-DD)
- `--contact-id INT` — связать с клиентом
- `--assignee TEXT` — исполнитель

### Примеры

```bash
ai-mini-box tasks list
# → 📋 Позвонить Ивану | high | deadline: 2026-06-25
#   📋 Отправить КП Анне | medium | deadline: 2026-06-27

ai-mini-box tasks add --title "Позвонить Ивану" --priority high --deadline 2026-06-25
# → ✅ Task added: Позвонить Ивану (high, deadline: 2026-06-25)

ai-mini-box tasks done --id 1
# → ✅ Task #1 completed
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `tasks` для внутреннего таск-трекера.

### Требования:
1. Typer с подкомандами: `list`, `add`, `done`, `delete`, `remind`
2. Новый репозиторий: `TaskRepo` (в core/repositories.py)
3. Новая модель: `Task` (title, description, priority, deadline, contact_id, assignee, status, created_at)
4. `remind`: настройка Telegram-напоминания о дедлайне
5. `--json` для машинного вывода
6. Фильтрация по статусу и приоритету

### Архитектура:
- Файл: `ai_mini_box/tools/tasks.py`
- Регистрация: `def register(app: typer.Typer)`
- Импорты: только из `ai_mini_box.core`, `ai_mini_box.infrastructure`

### Тесты:
1. Unit: MockTaskRepo — add, list, done, delete
2. Unit: фильтрация по статусу и приоритету
3. Integration: CliRunner — полный цикл
4. Smoke: --help

### Пример желаемого поведения:
```
$ ai-mini-box tasks list --status pending
📋 Позвонить Ивану | high | deadline: 2026-06-25
📋 Отправить КП | medium | deadline: 2026-06-27
```
```

### Тесты

- `test_tasks.py` — 4 unit-теста
- `test_tasks_integration.py` — 1 интеграционный
