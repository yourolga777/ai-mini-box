# Инструмент: backup

## Описание

Резервное копирование и восстановление базы данных. Использует `sqlite3.backup()` для создания консистентной копии без остановки сервиса.

### Команда

```bash
ai-mini-box backup COMMAND [OPTIONS]
```

### Подкоманды

| Команда | Описание |
|---------|----------|
| `create` | Создать бэкап |
| `list` | Список бэкапов |
| `restore` | Восстановить из бэкапа |
| `schedule` | Настроить авто-бэкап |
| `status` | Статус авто-бэкапа |

### Опции

**`backup create`:**
- `--output PATH` — путь для сохранения (default: data/backup/)
- `--name TEXT` — имя файла (default: app_YYYY-MM-DD_HHMMSS.db)
- `--compress` — сжать через gzip

**`backup list`:**
- `--limit N` — показать N последних
- `--json` — JSON-вывод

**`backup restore`:**
- `--file PATH` — файл бэкапа (обязательно)
- `--force` — без подтверждения

**`backup schedule`:**
- `--interval HOURS` — интервал в часах (default: 24)
- `--enable` | `--disable` — включить/отключить

### Примеры

```bash
ai-mini-box backup create
# → ✅ Backup created: data/backup/app_2026-06-21_153000.db (36 MB)

ai-mini-box backup list
# → 1. app_2026-06-21_153000.db | 2026-06-21 15:30 | 36 MB
#   2. app_2026-06-20_153000.db | 2026-06-20 15:30 | 35 MB

ai-mini-box backup create --compress
# → ✅ Backup created: data/backup/app_2026-06-21_154500.db.gz (12 MB)

ai-mini-box backup schedule --interval 12
# → ✅ Auto-backup enabled: every 12 hours

ai-mini-box backup restore --file data/backup/app_2026-06-20_153000.db --force
# → ✅ Database restored from backup (36 MB → 35 MB)
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `backup` для резервного копирования БД.

### Требования:
1. Typer с подкомандами: `create`, `list`, `restore`, `schedule`, `status`
2. Используй `BackupManager` из `infrastructure/backup/backup_manager.py`:
   - `create_backup(output_dir, db_path) -> Path`
   - `list_backups(backup_dir) -> list[BackupInfo]`
   - `restore_backup(backup_path, db_path)`
   - `schedule_auto(interval_hours)`
3. `BackupManager`: использует `sqlite3.backup()` для консистентности
4. `--compress`: сжатие gzip (для create)
5. `restore`: запрос подтверждения без `--force`
6. `schedule`: сохранение настройки в config.json (добавить поле auto_backup_interval)
7. Показывать размер бэкапов в читаемом формате (MB/GB)
8. При `restore` проверять, что файл существует и валидный SQLite

### Архитектура:
- Файл: `ai_mini_box/tools/backup.py`
- Регистрация: `def register(app: typer.Typer)` — `app.add_typer(backup_app, name="backup")`
- Использует `JsonConfigManager` для настроек авто-бэкапа
- Работает напрямую с sqlite3 (не через SQLAlchemy для консистентности)
- Не зависит от репозиториев

### Тесты:
1. Unit: create_backup в tmp_path
2. Unit: list показывает размер файлов
3. Unit: restore проверяет валидность SQLite
4. Integration: CliRunner — create → list → restore
5. Smoke: --help

### Структура файла:
```
tools/backup.py
```

### Пример желаемого поведения:
```
$ ai-mini-box backup create
✅ Backup: data/backup/app_2026-06-21_153000.db (36 MB)

$ ai-mini-box backup list
  1. app_2026-06-21_153000.db | 21.06 15:30 | 36.2 MB
  2. app_2026-06-20_153000.db | 20.06 15:30 | 35.8 MB

$ ai-mini-box backup restore --file data/backup/app_2026-06-20.db
⚠ Are you sure? [y/N]: y
✅ Database restored (35.8 MB)

$ ai-mini-box backup schedule --interval 12
✅ Auto-backup every 12 hours enabled
```
```

