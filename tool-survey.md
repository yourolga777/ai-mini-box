# Инструмент: survey

## Описание

Сбор обратной связи от клиентов: опросники после заказа/обращения, NPS (Net Promoter Score), статистика ответов. Помогает измерять качество сервиса.

### Команда

```bash
ai-mini-box survey COMMAND [OPTIONS]
```

### Подкоманды

| Команда | Описание |
|---------|----------|
| `create` | Создать опрос |
| `send` | Отправить опрос клиенту |
| `results` | Результаты опроса |
| `nps` | NPS-статистика |

### Опции

**`survey create`:**
- `--name TEXT` — название опроса
- `--questions TEXT` — вопросы через "|"
- `--target [order|complaint|all]` — когда отправлять

**`survey send`:**
- `--survey-id INT` (обязательно)
- `--contact-id INT` (обязательно)

**`survey nps`:**
- `--period [week|month|all]` — период
- `--json` — JSON-вывод

### Примеры

```bash
ai-mini-box survey create --name "После заказа" --questions "Оцените качество|Что улучшить?"
# → ✅ Survey #1 created: "После заказа" (2 questions)

ai-mini-box survey send --survey-id 1 --contact-id 1
# → ✅ Survey sent to Иван Петров

ai-mini-box survey nps --period month
# → 📊 NPS: 72 (promoters: 15, passives: 5, detractors: 3)
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `survey` для опросов и NPS.

### Требования:
1. Typer с подкомандами: `create`, `send`, `results`, `nps`
2. Новый репозиторий: `SurveyRepo` (в core/repositories.py)
3. Новые модели: `Survey`, `SurveyResponse`
4. NPS = % promoters (9-10) - % detractors (0-6)
5. Отправка через NotificationService или напрямую через каналы
6. Результаты: статистика ответов по каждому вопросу

### Архитектура:
- Файл: `ai_mini_box/tools/survey.py`
- Регистрация: `def register(app: typer.Typer)`
- Импорты: только из `ai_mini_box.core`, `ai_mini_box.infrastructure`

### Тесты:
1. Unit: MockSurveyRepo — create, send, nps calculation
2. Unit: NPS формула = correct
3. Integration: CliRunner — create → send → results
4. Smoke: --help

### Пример желаемого поведения:
```
$ ai-mini-box survey nps --period month
📊 NPS: 72 (promoters: 15, passives: 5, detractors: 3)
```
```

### Тесты

- `test_survey.py` — 3 unit-теста
- `test_survey_integration.py` — 1 интеграционный
