# Инструмент: crm-sync

## Описание

Синхронизация контактов, заказов и товаров с внешними CRM: AmoCRM, Bitrix24. Двусторонняя синхронизация по расписанию или по запросу.

### Команда

```bash
ai-mini-box crm-sync COMMAND [OPTIONS]
```

### Подкоманды

| Команда | Описание |
|---------|----------|
| `push` | Отправить данные во внешнюю CRM |
| `pull` | Забрать данные из внешней CRM |
| `status` | Статус последней синхронизации |
| `config` | Настройка подключения к CRM |

### Опции

**`crm-sync push`:**
- `--type [contacts|orders|products|all]` — что синхронизировать (default: all)
- `--crm [amo|bitrix]` — CRM

**`crm-sync pull`:**
- `--type [contacts|orders|products|all]`
- `--crm [amo|bitrix]`

**`crm-sync config`:**
- `--crm [amo|bitrix]` (обязательно)
- `--api-key TEXT` — API-ключ
- `--domain TEXT` — домен CRM (amo: your-domain.amocrm.ru)

### Примеры

```bash
ai-mini-box crm-sync push --type contacts --crm amo
# → ✅ Pushed 34 contacts to AmoCRM

ai-mini-box crm-sync pull --type orders --crm bitrix
# → ✅ Pulled 12 orders from Bitrix24

ai-mini-box crm-sync status
# → 🔄 AmoCRM:  last push 2026-06-21 15:30 | 34 contacts
#   Bitrix24: last pull 2026-06-21 14:00 | 12 orders
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `crm-sync` для синхронизации с внешними CRM.

### Требования:
1. Typer с подкомандами: `push`, `pull`, `status`, `config`
2. Поддержка AmoCRM REST API и Bitrix24 REST API
3. При push: читает из локальных репозиториев, отправляет в CRM
4. При pull: забирает из CRM, создаёт/обновляет локальные записи
5. Детектор конфликтов: если запись менялась в обоих местах — приоритет локальной
6. Статус синхронизации сохраняется в БД (SyncLogRepo)
7. API-ключи хранятся в config.json

### Архитектура:
- Файл: `ai_mini_box/tools/crm_sync.py`
- Регистрация: `def register(app: typer.Typer)`
- Новые модели: `SyncLog` (crm, type, direction, status, records_count, timestamp)
- Новый репозиторий: `SyncLogRepo`
- CRM-адаптеры: `ai_mini_box/tools/crm_adapters/`

### Тесты:
1. Unit: MockContactRepo + MockSyncLogRepo — push считает записи
2. Unit: pull создаёт новых контактов
3. Integration: CliRunner — config → push
4. Smoke: --help

### Пример желаемого поведения:
```
$ ai-mini-box crm-sync push --type contacts --crm amo
✅ Pushed 34 contacts to AmoCRM
```
```

### Тесты

- `test_crm_sync.py` — 3 unit-теста
- `test_crm_sync_integration.py` — 1 интеграционный
