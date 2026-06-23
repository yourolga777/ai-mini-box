# Инструмент: calendar

## Описание

Запись на услуги: расписание, свободные слоты, напоминания клиентам. Закрывает тему "График" из классификатора — можно отвечать на вопрос "Работаете в субботу?" не только текстом, но и предлагать запись.

### Команда

```bash
ai-mini-box calendar COMMAND [OPTIONS]
```

### Подкоманды

| Команда | Описание |
|---------|----------|
| `slots` | Показать свободные слоты |
| `book` | Записать клиента на время |
| `cancel` | Отменить запись |
| `list` | Список записей на день/неделю |
| `config` | Настройки графика работы |

### Опции

**`calendar slots`:**
- `--date DATE` — дата (YYYY-MM-DD)
- `--json` — JSON-вывод

**`calendar book`:**
- `--contact-id INT` (обязательно)
- `--datetime TEXT` — дата и время (YYYY-MM-DD HH:MM)
- `--service TEXT` — услуга

**`calendar config`:**
- `--start TEXT` — начало рабочего дня (default: 09:00)
- `--end TEXT` — конец рабочего дня (default: 18:00)
- `--slot-minutes INT` — длительность слота (default: 60)

### Примеры

```bash
ai-mini-box calendar slots --date 2026-06-25
# → 📅 2026-06-25: 5 свободных слотов
#   09:00 | 10:00 | 11:00 | 14:00 | 15:00

ai-mini-box calendar book --contact-id 1 --datetime "2026-06-25 10:00"
# → ✅ Booked: Иван Петров → 2026-06-25 10:00

ai-mini-box calendar list --date 2026-06-25
# → 📅 2026-06-25
#   10:00 | Иван Петров | Консультация
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `calendar` для записи на услуги.

### Требования:
1. Typer с подкомандами: `slots`, `book`, `cancel`, `list`, `config`
2. Новый репозиторий: `AppointmentRepo` (абстракция в core, реализация в infrastructure)
3. Новые модели: `Appointment` (contact_id, datetime, service, status)
4. Слоты рассчитываются из графика работы (config) и существующих записей
5. Настройки графика — из config.json (work_schedule_start/end)
6. Напоминания: опционально, через NotificationService

### Архитектура:
- Файл: `ai_mini_box/tools/calendar.py`
- Регистрация: `def register(app: typer.Typer)`
- Импорты: только из `ai_mini_box.core`, `ai_mini_box.infrastructure`

### Тесты:
1. Unit: MockAppointmentRepo — book, cancel, list
2. Unit: слоты = рабочие часы - занятые
3. Integration: CliRunner — book → list → cancel
4. Smoke: --help

### Пример желаемого поведения:
```
$ ai-mini-box calendar slots --date 2026-06-25
📅 2026-06-25: 5 слотов
09:00 | 10:00 | 11:00 | 14:00 | 15:00
```
```

### Тесты

- `test_calendar.py` — 3 unit-теста
- `test_calendar_integration.py` — 2 интеграционных
