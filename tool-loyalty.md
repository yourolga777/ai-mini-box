# Инструмент: loyalty

## Описание

Программа лояльности: бонусы за покупки, скидки постоянным клиентам, история начислений и списаний. Помогает удерживать клиентов и мотивировать повторные обращения.

### Команда

```bash
ai-mini-box loyalty COMMAND [OPTIONS]
```

### Подкоманды

| Команда | Описание |
|---------|----------|
| `balance` | Баланс бонусов контакта |
| `accrue` | Начислить бонусы |
| `spend` | Списать бонусы |
| `history` | История операций |
| `config` | Настройки программы (% начисления, мин. сумма) |

### Опции

**`loyalty balance`:**
- `--contact-id INT` (обязательно)

**`loyalty accrue`:**
- `--contact-id INT` (обязательно)
- `--amount INT` — бонусы в копейках
- `--reason TEXT` — причина

**`loyalty config`:**
- `--percent INT` — процент начисления от суммы заказа (default: 5)
- `--min-order INT` — мин. сумма заказа для начисления

### Примеры

```bash
ai-mini-box loyalty balance --contact-id 1
# → 🎯 Иван Петров: 1 250 бонусов (= 125₽)

ai-mini-box loyalty accrue --contact-id 1 --amount 500 --reason "Заказ #15"
# → ✅ Accrued 500 bonuses to Иван Петров

ai-mini-box loyalty config --percent 10
# → ✅ Loyalty: 5% → 10%
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `loyalty` для программы лояльности.

### Требования:
1. Typer с подкомандами: `balance`, `accrue`, `spend`, `history`, `config`
2. Новый репозиторий: `LoyaltyRepo` (абстракция в core, реализация в infrastructure)
3. Новые модели: `LoyaltyTransaction` (contact_id, amount, type, reason, date)
4. Настройки хранятся в config.json (поле loyalty)
5. Баланс рассчитывается как сумма всех accrual - сумма всех spending
6. `--json` для машинного вывода

### Архитектура:
- Файл: `ai_mini_box/tools/loyalty.py`
- Регистрация: `def register(app: typer.Typer)`
- Импорты: только из `ai_mini_box.core`, `ai_mini_box.infrastructure`

### Тесты:
1. Unit: MockLoyaltyRepo — accrue, balance, history
2. Unit: баланс = сумма начислений - списаний
3. Integration: CliRunner — полный цикл
4. Smoke: --help

### Пример желаемого поведения:
```
$ ai-mini-box loyalty balance --contact-id 1
🎯 Иван Петров: 1 250 бонусов
```
```

### Тесты

- `test_loyalty.py` — 3 unit-теста
- `test_loyalty_integration.py` — 1 интеграционный
