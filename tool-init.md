# Инструмент: init

## Описание

Инициализация проекта: создание config.json, БД, директорий data/ и models/. Запускается один раз при первом развёртывании.

### Команда

```bash
ai-mini-box init [OPTIONS]
```

### Опции

| Опция | Описание |
|-------|----------|
| `--force` | Перезаписать существующий config.json |
| `--config PATH` | Путь для config.json (default: data/config.json) |
| `--db PATH` | Путь для БД (default: data/app.db) |

### Примеры

```bash
ai-mini-box init
# → ✅ Project initialized: data/config.json, data/app.db, data/backup/

ai-mini-box init --force
# → ✅ Configuration reset to defaults

ai-mini-box init --config custom/config.json
# → ✅ Project initialized: custom/config.json
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `init` для инициализации проекта.

### Требования:
1. Typer-команда (не подкоманда, а часть главной app)
2. Создаёт директории: data/, data/backup/, data/models/, data/training/
3. Создаёт `data/config.json` со значениями по умолчанию (через JsonConfigManager)
4. Создаёт БД: вызывает `init_db()` из infrastructure/database.py
5. Если файлы уже существуют — пропустить (кроме --force)
6. Вывести список созданных файлов и директорий
7. Только `init` — не требует активации никаких других сервисов

### Архитектура:
- Использует `JsonConfigManager` из `ai_mini_box.infrastructure.config`
- Использует `init_db` из `ai_mini_box.infrastructure.database`
- Файл: `ai_mini_box/tools/init.py`
- Регистрация: `def register(app: typer.Typer)` — добавляет команду `init` напрямую в app

### Тесты:
1. Unit: проверить создание директорий через tmp_path
2. Unit: проверить, что config.json создаётся с дефолтными значениями
3. Unit: --force перезаписывает существующий config
4. Integration: CliRunner + invoke(["init"]) → exit_code=0

### Пример желаемого поведения:
```
$ ai-mini-box init
✅ Created: data/config.json
✅ Created: data/app.db
✅ Created: data/backup/
✅ Created: data/models/
✅ Created: data/training/

$ ai-mini-box init --force
✅ Configuration reset to defaults
```
```

### Тесты

- `test_init.py` — 3 unit-теста (создание, --force, пропуск существующих)
- `test_init_integration.py` — 1 интеграционный тест (CliRunner)
- `MockRepo`: не требуется
