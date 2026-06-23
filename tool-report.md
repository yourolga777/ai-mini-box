# Инструмент: report

## Описание

Генерация отчётов и статистики: топ-5 тем, timeline обращений, экспорт в CSV и PNG-графики.

Использует pandas + matplotlib для расчётов и визуализации.

### Команда

```bash
ai-mini-box report COMMAND [OPTIONS]
```

### Подкоманды

| Команда | Описание |
|---------|----------|
| `topics` | Статистика распределения по темам |
| `timeline` | График обращений по дням/неделям |
| `export` | Экспорт данных в CSV |
| `full` | Полный отчёт (всё сразу) |

### Опции

**`report topics`:**
- `--from DATE` | `--to DATE` — период
- `--limit N` — сколько тем показать (default: 5)
- `--json` | `--png PATH` — вывод

**`report timeline`:**
- `--from DATE` | `--to DATE` — период
- `--granularity [day|week|month]` — детализация
- `--png PATH` — сохранить график

**`report export`:**
- `--format [csv|json]` — формат (default: csv)
- `--output PATH` — путь для сохранения
- `--type [messages|contacts|products]` — что экспортировать

**`report full`:**
- `--output PATH` — директория для сохранения отчёта
- `--png` — с графиками

### Примеры

```bash
ai-mini-box report topics
# → 📊 Распределение по темам (всего: 145 сообщений)
#   Цены:    45 (31.0%) ████████████
#   Заказ:   38 (26.2%) ██████████
#   Жалоба:  25 (17.2%) ██████
#   Другое:  22 (15.2%) ██████
#   График:  15 (10.3%) ████

ai-mini-box report timeline --granularity week --png report.png
# → ✅ Timeline saved to report.png

ai-mini-box report export --format csv --output messages.csv
# → ✅ Exported 145 messages to messages.csv
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `report` для генерации отчётов и статистики.

### Требования:
1. Typer с подкомандами: `topics`, `timeline`, `export`, `full`
2. Используй существующий `ReportService` из `core/services/report_service.py`:
   - `topic_distribution(from_date, to_date) -> dict[str, int]`
   - `message_timeline(from_date, to_date, granularity) -> list[tuple[str, int]]`
   - `export_csv(data_type, output_path) -> str`
3. Используй `chart_renderer` из `infrastructure/reports/chart_renderer.py`:
   - `plot_timeline(timeline_data, save_path)`
   - `plot_topic_pie(topic_distribution, save_path)`
4. Период: `--from` и `--to` в формате YYYY-MM-DD
5. `--json`: машинный вывод
6. `--png`: сохранение графика в файл
7. Для `timeline`: cli-вывод в виде ASCII-гистограммы
8. Для `export`: поддержка CSV и JSON

### Архитектура:
- Файл: `ai_mini_box/tools/report.py`
- Регистрация: `def register(app: typer.Typer)` — `app.add_typer(report_app, name="report")`
- Использует `MessageRepo` и `OrderRepo` из `ai_mini_box.core.repositories`
- pandas + matplotlib для графиков
- Зависимости: pandas, matplotlib

### Тесты:
1. Unit: MockMessageRepo — topics distribution
2. Unit: MockMessageRepo — timeline
3. Unit: export в CSV/JSON
4. Integration: CliRunner — topics + timeline + export
5. Smoke: --help

### Структура файла:
```
tools/report.py
```

### Пример желаемого поведения:
```
$ ai-mini-box report topics
📊 Всего: 145 сообщений
Цены     ████████████████████ 45 (31%)
Заказ    ████████████████     38 (26%)
Жалоба   ██████████          25 (17%)
Другое   █████████           22 (15%)
График   ██████              15 (10%)

$ ai-mini-box report timeline --granularity month --png stats.png
✅ Timeline saved to stats.png
```
```

