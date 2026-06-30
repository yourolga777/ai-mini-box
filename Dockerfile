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
RUN pip install --no-cache-dir ./packages/web/[analytics]
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
