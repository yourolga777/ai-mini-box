# Инструмент: analytics

## Описание

Продвинутая аналитика: LTV клиентов, конверсия сообщений в заказы, Retention (возврат клиентов), прогнозы на основе исторических данных. Использует pandas + matplotlib.

### Команда

```bash
ai-mini-box analytics COMMAND [OPTIONS]
```

### Подкоманды

| Команда | Описание |
|---------|----------|
| `ltv` | LTV (Lifetime Value) клиентов |
| `retention` | Возвращаемость клиентов |
| `conversion` | Конверсия: сообщение → заказ |
| `forecast` | Прогноз на N дней |

### Опции

**`analytics ltv`:**
- `--top N` — показать N клиентов с макс. LTV
- `--json` | `--png PATH` — вывод
- `--from DATE` | `--to DATE` — период

**`analytics retention`:**
- `--period [week|month]` — период
- `--json` | `--png PATH`

**`analytics forecast`:**
- `--days N` — на сколько дней прогноз (default: 30)
- `--png PATH` — сохранить график

### Примеры

```bash
ai-mini-box analytics ltv --top 5
# → 📊 LTV (Lifetime Value)
#   1. Иван Петров     | 45 000₽
#   2. Анна Смирнова   | 32 000₽

ai-mini-box analytics retention --png retention.png
# → ✅ Retention chart saved to retention.png

ai-mini-box analytics forecast --days 30 --png forecast.png
# → ✅ Forecast saved to forecast.png
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `analytics` для продвинутой аналитики.

### Требования:
1. Typer с подкомандами: `ltv`, `retention`, `conversion`, `forecast`
2. Использует репозитории из `ai_mini_box.core.repositories`
3. LTV = сумма всех заказов клиента (из OrderRepo)
4. Retention = % клиентов, сделавших >1 заказа за период
5. Conversion = отношение числа заказов к числу сообщений
6. Forecast = линейная регрессия (sklearn) или скользящее среднее
7. `--png`: matplotlib график
8. `--json`: машинный вывод

### Архитектура:
- Файл: `ai_mini_box/tools/analytics.py`
- Регистрация: `def register(app: typer.Typer)`
- Импорты: только из `ai_mini_box.core`, `ai_mini_box.infrastructure`

### Тесты:
1. Unit: MockOrderRepo + MockMessageRepo — LTV расчёт
2. Unit: conversion = correct ratio
3. Integration: CliRunner — --json вывод
4. Smoke: --help

### Пример желаемого поведения:
```
$ ai-mini-box analytics ltv --top 3
📊 LTV (Lifetime Value)
1. Иван Петров     | 45 000 ₽
2. Анна Смирнова   | 32 000 ₽
3. Олег Иванов     | 28 500 ₽
```
```

### Тесты

- `test_analytics.py` — 3 unit-теста (LTV, retention, conversion)
- `test_analytics_integration.py` — 1 интеграционный
