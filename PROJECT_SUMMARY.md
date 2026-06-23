# AI mini box — Project Summary

## Overview

**AI mini box** — modular, service-oriented Python system for small business automation. Monorepo with 4 packages, PWA web interface, plugin-based architecture (entry points).

## Packages

| Package | Version | PyPI | Description |
|---|---|---|---|
| `ai-mini-box-core` | 5.0.0 | ✅ | Core: CLI, config, DB (SQLAlchemy), models, repositories |
| `ai-mini-box-web` | 0.1.0 | ✅ | FastAPI server + React 18 PWA frontend |
| `ai-mini-box-telegram` | 0.1.0 | ✅ | Telegram integration (poll/daemon via Bot API) |
| `ai-mini-box-demo` | — | ❌ | Demo/test commands |

## Repository

- **GitHub:** `yourolga777/ai-mini-box`
- **Branches:** `main` (stable), `develop` (active)
- **Tags:** `v5.0.0`, `web-v0.1.0`
- **CI:** GitHub Actions — tests (3.12/3.13) + PyPI auto-publish on tag

## Architecture

```
D:\Projects\AI box 4.0\
├── packages/
│   ├── core/        — ai_mini_box (CLI, models, repos, config, migrations)
│   ├── web/         — FastAPI + React PWA, entry point: web
│   ├── telegram/    — Telegram bot, entry point: telegram
│   └── demo/        — demo tools, entry point: demo
├── data/            — runtime data (DB, config, logs, uploads)
├── docs/plugins/    — plugin developer guide (9 .md files)
├── run.bat          — one-click launch (editable install + server)
├── stop.bat         — kill server by PID
└── PROJECT_SUMMARY.md
```

## Tech Stack

- **Python ≥3.12**, SQLAlchemy 2.0+, Pydantic v2, Typer, FastAPI
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS 4, TanStack React Query, Zustand
- **DB:** SQLite via SQLAlchemy + Alembic migrations
- **Config:** JSON config file (`data/config.json`), env var overrides (`AI_BOX_*`)
- **CLI:** `python -m ai_mini_box <command>` — init, serve, config, db
- **Plugins:** `importlib.metadata` entry points (`ai_mini_box.tools`, `ai_mini_box.help`)

## API Routes

| Method | Path | Description |
|---|---|---|
| GET | `/api/contacts` | List contacts |
| POST | `/api/contacts` | Create contact |
| GET | `/api/contacts/{id}` | Get contact |
| PUT | `/api/contacts/{id}` | Update contact |
| DELETE | `/api/contacts/{id}` | Delete contact |
| GET | `/api/products` | List products |
| POST | `/api/products` | Create product |
| GET | `/api/products/{id}` | Get product |
| PUT | `/api/products/{id}` | Update product |
| DELETE | `/api/products/{id}` | Delete product |
| GET | `/api/messages` | List messages |
| GET | `/api/orders` | List orders |
| GET | `/api/plugins` | List plugins |
| GET | `/api/plugins/{name}` | Get plugin info |
| GET | `/api/plugins/{name}/logs` | Get plugin logs |
| POST | `/api/plugins/install` | Install from PyPI |
| POST | `/api/plugins/install/upload` | Upload & install wheel |
| DELETE | `/api/plugins/{name}` | Uninstall plugin |
| POST | `/api/plugins/{name}/start` | Start daemon |
| POST | `/api/plugins/{name}/stop` | Stop daemon |
| GET | `/api/help` | Dynamic help sections |
| GET | `/api/plugins/config` | Get config |
| POST | `/api/plugins/config/set` | Set config value |

## Frontend Pages

- `/` — Dashboard
- `/contacts` — Contact management
- `/products` — Product catalog
- `/messages` — Messages
- `/orders` — Orders
- `/plugins` — Plugin manager (list, install, uninstall, daemon)
- `/plugins/:name` — Plugin detail
- `/help` — Dynamic help from Markdown files

## How to Run

```bash
run.bat
# Installs packages editable, starts server at http://127.0.0.1:8080
```

Or manually:
```bash
pip install -e packages/core/
pip install -e packages/web/
python -m ai_mini_box init
python -m ai_mini_box serve
```

## How to Publish a New Release

```bash
# 1. Update version in pyproject.toml
# 2. Commit & tag
git add -A
git commit -m "release: ai-mini-box-core X.Y.Z"
git tag vX.Y.Z
git push --tags origin develop
# 3. CI auto-publishes to PyPI
# 4. Merge to main:
git checkout main
git merge develop
git push origin main
```

## Plugin System

Plugins are discovered via entry point `ai_mini_box.tools`. Each plugin registers CLI commands.

Registered plugins:
- `web` — FastAPI server via `ai_mini_box_web.commands:register`
- `telegram` — Telegram polling via `ai_mini_box_telegram.commands:register`

Help content loads dynamically from `help/*.md` + plugin entry points (`ai_mini_box.help`).

## CI/CD

- **tests.yml:** Runs pytest per package (core, web, telegram, demo) on Python 3.12/3.13
- **publish.yml:** Builds wheel + publishes to PyPI on tag push (uses `__token__` auth)

## Key Decisions

- **Prices as integer kopecks** (not float)
- **Sync SQLAlchemy + sync FastAPI endpoints** (no async in core)
- **Plugin model:** separate repos (Option B), publish independently
- **Dynamic help system:** entry points + Markdown files
- **Port 8080** (changed from 8000 to avoid BrandForge conflict)
- **No trailing slashes** in API routes (`/api/contacts`, not `/api/contacts/`)

## Runbook

| Action | Command |
|---|---|
| Init project | `python -m ai_mini_box init` |
| Start server | `python -m ai_mini_box serve` or `run.bat` |
| Stop server | `stop.bat` or Ctrl+C |
| Run tests | `pytest packages/core/ tests/` (or per package) |
| Apply migrations | `python -m ai_mini_box db upgrade` |
| View config | `python -m ai_mini_box config show` |
| Set config | `python -m ai_mini_box config set <key> <value>` |
| List tasks | `.tausik/tausik task list` |
| Check warnings | `.tausik/tausik status` |

## Known Issues

- 3 pre-existing test failures in `test_update_checker.py` (mock/urllib issue)
- GitHub PAT expires **22 July 2026** — renew before date
- `PYPI_TOKEN` stored in GitHub Secrets for CI auto-publish
