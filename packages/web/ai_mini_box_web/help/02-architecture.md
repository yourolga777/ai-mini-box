# Architecture

## Overview

ai-mini-box is a modular monorepo for small business automation. It provides a layered Python core with domain models, infrastructure, CLI, and a plugin system — plus a web interface (PWA) built on FastAPI + React.

## Project structure

```
ai-mini-box/
├── packages/
│   ├── core/              # Domain + infrastructure layer
│   │   └── ai_mini_box/
│   │       ├── core/          # Pydantic models, ABC repos, DI container
│   │       ├── infrastructure/ # SQLAlchemy ORM, config, logger, DB
│   │       ├── migrations/    # Alembic migrations (bundled)
│   │       └── cli.py         # Typer CLI + plugin loader
│   ├── web/               # FastAPI backend + React SPA
│   │   ├── ai_mini_box_web/
│   │   │   ├── routers/       # CRUD endpoints (contacts, products…)
│   │   │   ├── services/      # Plugin manager
│   │   │   ├── static/        # Built frontend assets
│   │   │   └── server.py      # FastAPI app factory
│   │   └── frontend/          # React + Vite + Tailwind + React Query
│   └── demo/              # Example plugin service
├── tool-*.md             # 30 service specifications
├── run.bat               # One-click run (Windows)
└── .github/workflows/    # CI + publish to PyPI
```

## Layer architecture

### Core layer — `packages/core/ai_mini_box/core/`

- `models.py` — Pydantic v2 models: Contact, Product, Message, Order. Prices stored as integer kopecks.
- `repositories.py` — ABCs with QueryBuilder (method-chaining filter/search/sort/limit/offset).
- `container.py` — RepoContainer (DI) and AppContext (global singleton for CLI).
- `exceptions.py` — Custom domain exceptions.

### Infrastructure layer — `packages/core/ai_mini_box/infrastructure/`

- `database.py` — SQLAlchemy engine, `get_db()` context manager (auto-commit/rollback).
- `config.py` — JsonConfigManager with Fernet encryption for sensitive fields.
- `orm_models.py` — SQLAlchemy declarative models.
- `mapping.py` — Pydantic-to-ORM mapper.
- `logger.py` — Loguru setup with rotation (1 MB x 3 files).
- `repositories/` — SQLAlchemy implementations of ABC repos.

### Presentation layer

- **CLI:** Typer app in `cli.py`, auto-loads plugins via entry points `ai_mini_box.tools`.
- **Web API:** FastAPI with CRUD routers for contacts, products, messages, orders + Swagger UI at `/docs`.
- **Frontend:** React 18 SPA with TypeScript, Vite, Tailwind CSS, React Query. Built into `static/`.

## Plugin system

Any package can register CLI commands via the entry point group `ai_mini_box.tools`. The web interface also discovers plugins at runtime and shows their status on the Plugins page.

To create a plugin:

```toml
# pyproject.toml
[project.entry-points."ai_mini_box.tools"]
my_service = "my_package.commands:register"
```

The `register(app)` function receives a Typer instance and adds subcommands.

## Tech stack

| Category | Technology |
|---|---|
| Language | Python ≥3.12 |
| ORM | SQLAlchemy 2.0+ |
| Validation | Pydantic v2 |
| Web API | FastAPI + Uvicorn |
| Frontend | React 18 + TypeScript |
| Build | Vite + Tailwind |
| Data | React Query (@tanstack) |
| Database | SQLite (default) |
| CLI | Typer |
| Migrations | Alembic |
| Encryption | cryptography (Fernet) |
| Logging | loguru |

## Key patterns

- **Repository pattern:** Abstract base classes in `core/`, SQLAlchemy implementations in `infrastructure/repositories/`. Swap with mocks for testing.
- **Dependency injection:** `RepoContainer(session)` — single entry point for all repos. Used with `with get_db() as session: repos = RepoContainer(session)`.
- **QueryBuilder:** In-memory filtering on lists of Pydantic models. Supports `.filter()`, `.search()`, `.sort()`, `.limit()`, `.offset()`.
- **Migrations bundled:** Alembic migrations live inside the installed package. `ai-mini-box db upgrade` runs them programmatically.

## Domain model

| Entity | Key fields | Relations |
|---|---|---|
| Contact | name, phone, email, telegram_id | has messages, has orders |
| Product | name, price (kopecks) | — |
| Message | content, source (telegram/email/…), topic | belongs to Contact |
| Order | status, items, total | belongs to Contact |

## Testing

**96 tests total** (74 core + 13 web + 9 demo)

- Core: unit tests (config, logger) + integration (CLI commands, repos, DB)
- Web: API endpoints via FastAPI TestClient with tmp_path DB
- Demo: E2E with CliRunner
- All use in-memory or temp-file SQLite
