# Инструмент: web

## Описание

Встроенный веб-интерфейс (FastAPI + Jinja2). Работает в браузере на localhost — альтернатива PyQt6 GUI для пользователей, которые не хотят устанавливать десктопное приложение.

### Команда

```bash
ai-mini-box web [OPTIONS]
```

### Опции

| Опция | Описание |
|-------|----------|
| `--host TEXT` | Хост (default: 127.0.0.1) |
| `--port INT` | Порт (default: 8080) |
| `--config PATH` | Путь к config.json |
| `--debug` | Режим отладки |
| `--open-browser` | Открыть браузер автоматически |

### Примеры

```bash
ai-mini-box web
# → [INFO] Web UI: http://127.0.0.1:8080

ai-mini-box web --port 3000 --open-browser
# → [INFO] Opening browser: http://127.0.0.1:3000
```

### Страницы

| URL | Описание |
|-----|----------|
| `/` | Дашборд: статистика, последние сообщения |
| `/contacts` | Список контактов |
| `/products` | Список товаров |
| `/orders` | Список заказов |
| `/messages` | История сообщений |
| `/settings` | Настройки (config) |

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `web` для запуска веб-интерфейса.

### Требования:
1. Typer-команда (без подкоманд)
2. FastAPI + Jinja2 (обязательные зависимости: fastapi, uvicorn, jinja2)
3. Страницы: дашборд, контакты, товары, заказы, сообщения, настройки
4. Использует репозитории из `ai_mini_box.core.repositories` для данных
5. Использует `JsonConfigManager` для чтения/записи настроек
6. `--open-browser`: открыть браузер через webbrowser.open
7. Graceful shutdown: Ctrl+C останавливает uvicorn

### Архитектура:
- Файл: `ai_mini_box/tools/web.py`
- Регистрация: `def register(app: typer.Typer)`
- Веб-шаблоны: `ai_mini_box/tools/web/templates/`
- Статика: `ai_mini_box/tools/web/static/`

### Тесты:
1. Unit: импорт FastAPI приложения
2. Integration: TestClient из FastAPI — проверить /, /contacts, /products
3. Smoke: --help показывает опции

### Пример желаемого поведения:
```
$ ai-mini-box web
[INFO] Starting web UI...
[INFO] Web UI: http://127.0.0.1:8080 (Ctrl+C to stop)
```
```

### Тесты

- `test_web.py` — 1 unit (импорт)
- `test_web_integration.py` — 3 теста (GET /, GET /contacts, GET /products)
