# Спецификация: Развёртывание (Docker, .env, сборка)

## Распределение по разработчикам

| Компонент | Раздел | Разработчик |
|---|---|---|
| `Dockerfile` (web) + frontend-сборка | §1 | **Web** |
| `Dockerfile.telegram` | §2 | **Telegram** |
| `Dockerfile.llm` | §3 | **LLM** |
| `docker-compose.yml` | §4 | **Web** |
| `docker-entrypoint.sh` (init + migrate) | §1 | **Core** |
| `GET /api/health` | §7 | **Web** |
| `.env.example` | §5 | **Web / DevOps** |
| GitHub Actions (docker.yml) | §6 | **Web / DevOps** |
| CORS / rate limiting / nginx | §8 | **Web** |

## 1. Dockerfile (web) — Web-разработчик

```dockerfile
# Stage 1: Frontend build
FROM node:20-alpine AS frontend
WORKDIR /build/frontend
COPY packages/web/frontend/package*.json ./
RUN npm ci
COPY packages/web/frontend/ ./
RUN npm run build

# Stage 2: Backend build
FROM python:3.12-slim AS backend
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*
COPY packages/core/ ./packages/core/
RUN pip install --no-cache-dir ./packages/core/
COPY packages/web/ ./packages/web/
RUN pip install --no-cache-dir ./packages/web/
COPY --from=frontend /build/frontend/dist/ ./packages/web/ai_mini_box_web/static/

# Stage 3: Runtime
FROM python:3.12-slim AS runtime
WORKDIR /data
COPY --from=backend /app /app
COPY --from=backend /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend /usr/local/bin /usr/local/bin
EXPOSE 8080
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["serve"]
```

**docker-entrypoint.sh (Core-разработчик):**
```bash
#!/bin/sh
set -e
python -m ai_mini_box init --non-interactive
python -m alembic upgrade head
exec python -m ai_mini_box "$@"
```

## 2. Dockerfile.telegram — Telegram-разработчик

Аналогично, но:
- Без frontend-стадии
- Ставится `ai-mini-box-telegram`
- `CMD ["python", "-m", "ai_mini_box", "telegram", "poll"]`

## 3. Dockerfile.llm — LLM-разработчик

Аналогично, но:
- Ставится `ai-mini-box-llm`
- `CMD` — см. spec `09-llm-process-daemon-spec.md` (новая команда `llm process-daemon`)

## 4. docker-compose.yml — Web-разработчик

```yaml
version: "3.9"
services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    volumes:
      - data:/data
    environment:
      - AI_BOX_DB_PATH=/data/app.db
      - AI_BOX_HOST=0.0.0.0
      - AI_BOX_PORT=8080
      - AI_BOX_SECRET=${AI_BOX_SECRET:-changeme}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/health')"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s

  telegram:
    build:
      context: .
      dockerfile: Dockerfile.telegram
    volumes:
      - data:/data
    environment:
      - AI_BOX_DB_PATH=/data/app.db
      - AI_BOX_SECRET=${AI_BOX_SECRET:-changeme}
    depends_on:
      web:
        condition: service_healthy
    restart: unless-stopped

  llm:
    build:
      context: .
      dockerfile: Dockerfile.llm
    volumes:
      - data:/data
      - models:/models
    environment:
      - AI_BOX_DB_PATH=/data/app.db
      - AI_BOX_SECRET=${AI_BOX_SECRET:-changeme}
    depends_on:
      web:
        condition: service_healthy
    restart: unless-stopped

volumes:
  data:
  models:
```

## 5. `.env.example` — Web-разработчик / DevOps

```bash
AI_BOX_SECRET=
AI_BOX_DB_PATH=/data/app.db
AI_BOX_HOST=0.0.0.0
AI_BOX_PORT=8080
AI_BOX_LOG_LEVEL=info
```

Сгенерировать SECRET:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 6. GitHub Actions (docker.yml) — Web-разработчик / DevOps

Триггер: push tag `v*`.
Сборка и публикация в GHCR трёх образов: web, telegram, llm.

## 7. Healthcheck — Web-разработчик

Добавить `GET /api/health` в `server.py`:
```python
@app.get("/api/health")
def health():
    return {"status": "ok", "version": "5.0.1"}
```

## 8. Production checklist — Web-разработчик

- [ ] CORS: `allow_origins=["*"]` → конкретный домен
- [ ] Rate limiting (slowapi)
- [ ] nginx reverse proxy (опционально)
- [ ] Бэкап БД (cron + sqlite3 .backup)
- [ ] Telegram webhook вместо polling (если есть публичный URL)

## 9. Критерии приёмки

- `docker compose build` собирает все 3 образа
- `docker compose up -d` запускает все сервисы
- `GET /api/health` возвращает 200
- Telegram-бот работает в контейнере
- LLM-процессор работает в контейнере
- Данные сохраняются при перезапуске (persistent volume)
- `docker compose down` + `docker compose up -d` — данные не теряются
