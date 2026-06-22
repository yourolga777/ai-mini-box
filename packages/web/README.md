# ai-mini-box-web

Web interface (PWA) for [ai-mini-box-core](https://pypi.org/project/ai-mini-box-core/).

## Quick start

```bash
pip install ai-mini-box-web
ai-mini-box init
ai-mini-box serve
```

Open http://127.0.0.1:8000

## Features

- Dashboard with entity counters
- Contacts, Products, Messages, Orders — CRUD via API
- Plugin dashboard — list installed plugins, view status and logs
- Built-in Swagger UI at `/docs`

## Development

```bash
pip install -e packages/web[dev]
cd packages/web/frontend
npm run dev     # hot-reload frontend
```

Backend and frontend run separately during development (Vite proxies `/api` to FastAPI).
