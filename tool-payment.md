# Инструмент: payment

## Описание

Приём платежей: интеграция с платёжными системами (ЮКасса, Tinkoff, Сбербанк). Создание ссылок на оплату, проверка статуса, история транзакций.

### Команда

```bash
ai-mini-box payment COMMAND [OPTIONS]
```

### Подкоманды

| Команда | Описание |
|---------|----------|
| `link` | Создать ссылку на оплату |
| `status` | Проверить статус платежа |
| `history` | История платежей |
| `config` | Настройка платёжной системы |

### Опции

**`payment link`:**
- `--order-id INT` (обязательно)
- `--amount INT` — сумма в копейках (если не из заказа)
- `--description TEXT` — описание платежа
- `--provider [yookassa|tinkoff|sber]` — провайдер (default: из config)

**`payment status`:**
- `--payment-id TEXT` (обязательно) — ID транзакции

**`payment config`:**
- `--provider [yookassa|tinkoff|sber]`
- `--api-key TEXT` — API-ключ/секрет
- `--shop-id TEXT` — ID магазина

### Примеры

```bash
ai-mini-box payment link --order-id 12 --amount 450000
# → 🔗 Ссылка на оплату: https://pay.yookassa.com/xxx (4 500₽)

ai-mini-box payment status --payment-id "xxx"
# → 💳 Платёж xxx: succeeded (4 500₽) | 2026-06-21 15:30

ai-mini-box payment config --provider yookassa --shop-id "12345"
# → ✅ YooKassa configured: shop-id=12345
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `payment` для приёма платежей.

### Требования:
1. Typer с подкомандами: `link`, `status`, `history`, `config`
2. Поддержка YooKassa, Tinkoff, Сбербанк (через их HTTP API)
3. При успешном платеже — обновлять статус заказа → completed
4. При успешном платеже — отправлять уведомление (через NotificationService)
5. Данные провайдера хранятся в config.json
6. История платежей — в БД (PaymentRepo)

### Архитектура:
- Файл: `ai_mini_box/tools/payment.py`
- Регистрация: `def register(app: typer.Typer)`
- Новые модели: `Payment` (id, order_id, amount_kopecks, provider, status, created_at)
- Новый репозиторий: `PaymentRepo`
- Провайдеры: `ai_mini_box/tools/providers/`

### Тесты:
1. Unit: MockPaymentRepo — link, status, history
2. Unit: успешный платёж → order status = completed
3. Integration: CliRunner — ссылка на оплату
4. Smoke: --help

### Пример желаемого поведения:
```
$ ai-mini-box payment link --order-id 12
🔗 Ссылка на оплату: https://pay.yookassa.com/xxx (4 500 ₽)
```
```

### Тесты

- `test_payment.py` — 3 unit-теста
- `test_payment_integration.py` — 1 интеграционный
