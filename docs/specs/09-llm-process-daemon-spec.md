# Спецификация: LLM process-daemon

**Разработчик:** LLM-разработчик

**Файлы:**
- `packages/llm/ai_mini_box_llm/plugin.py` — новая подкоманда
- `packages/llm/ai_mini_box_llm/daemon.py` — новый файл (опционально)

## Описание

Требуется новая CLI-команда `llm process-daemon` — бесконечный цикл, который периодически запускает `AutoProcessor.process_all()` для автоматической обработки нераспределённых сообщений.

**Назначение:** Запуск в отдельном Docker-контейнере (спецификация `07-devops-deployment-spec.md`, §3).

## Интерфейс

```bash
ai-mini-box llm process-daemon [--interval 60]
```

## Требования

```python
@app.command()
def process_daemon(
    ctx: typer.Context,
    interval: int = typer.Option(60, "--interval", "-i", help="Пауза между циклами (сек)"),
):
    """
    Daemon: бесконечный цикл обработки сообщений через AutoProcessor.
    Завершить — Ctrl+C (SIGINT) или SIGTERM (контейнер).
    """
```

## Логика

```python
import time
import signal
from loguru import logger

running = True

def _shutdown(sig, frame):
    global running
    logger.info("Received signal {}, shutting down...", sig)
    running = False

signal.signal(signal.SIGTERM, _shutdown)
signal.signal(signal.SIGINT, _shutdown)

logger.info("Process daemon started (interval={}s)", interval)

while running:
    try:
        # Получаем сервисы из реестра
        auto_processor = get_service("auto_processor")
        if auto_processor:
            count = auto_processor.process_all()
            logger.info("Processed {} messages", count)
        else:
            logger.warning("AutoProcessor not registered")
    except Exception as e:
        logger.error("Process cycle failed: {}", e)

    # Ожидание с поддержкой прерывания
    for _ in range(interval):
        if not running:
            break
        time.sleep(1)

logger.info("Process daemon stopped")
```

## Graceful shutdown

- `SIGTERM` — корректное завершение (контейнер docker stop)
- `SIGINT` — Ctrl+C при ручном запуске
- Таймаут: не более `interval` секунд (пауза разбита на 1-секундные слоты)

## Зависимости

- `AutoProcessor` из `core/services/auto_processor.py`
- `get_service()` из `core/services/registry.py`
- Никаких новых внешних зависимостей

## Dockerfile

```dockerfile
# packages/llm/Dockerfile.llm — LLM-разработчик
FROM python:3.12-slim
WORKDIR /app

# Копируем core (зависимость)
COPY packages/core/ ./packages/core/
RUN pip install --no-cache-dir ./packages/core/

# Копируем llm-плагин
COPY packages/llm/ ./packages/llm/
RUN pip install --no-cache-dir ./packages/llm/

CMD ["python", "-m", "ai_mini_box", "llm", "process-daemon"]
```

## Критерии приёмки

- `ai-mini-box llm process-daemon --interval 10` запускает цикл
- Каждые 10 секунд вызывается `AutoProcessor.process_all()`
- `Ctrl+C` завершает процесс с логом `"Process daemon stopped"`
- `docker stop` контейнера завершает процесс через SIGTERM
- Если AutoProcessor не зарегистрирован — лог `warning` и продолжение цикла
- Ошибки внутри `process_all()` не прерывают цикл (лог + continue)
