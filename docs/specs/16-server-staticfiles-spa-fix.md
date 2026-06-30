# Спецификация: SPA-роутинг — StaticFiles коррекция (v1)

**Разработчик:** Веб (backend — `server.py`)  
**Приоритет:** P0 (блокирует навигацию по плагинам)  
**Статус:** К реализации  

---

## Проблема

При переходе на `/plugins/llm` (и любой SPA-роут) сервер возвращает `{"detail":"Not Found"}`.

**Коренная причина:** `server.py:76` монтирует `StaticFiles` в корень `/`:

```python
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
```

Starlette обрабатывает mount до всех остальных маршрутов. Когда приходит запрос на `/plugins/llm`, `StaticFiles` ищет файл `static/plugins/llm` — не находит → возвращает 404. Кэтч-олл `serve_spa()` на строке 79 **не вызывается**, т.к. mount уже вернул ответ.

Попутная проблема: браузер запрашивает `/favicon.ico` → 404 (в логах `favicon.ico:1 Failed to load resource`).

---

## Структура static/

```
packages/web/ai_mini_box_web/static/
├── index.html              → ссылается на /assets/index-xxx.js, /favicon.svg
├── favicon.svg             → корневой статический файл
├── icons.svg
└── assets/
    ├── index-CaeyohaM.js   → JS-бандл
    └── index-DEO9ulpQ.css  → CSS-бандл
```

`index.html` содержит:
```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
<script type="module" crossorigin src="/assets/index-CaeyohaM.js"></script>
<link rel="stylesheet" crossorigin href="/assets/index-DEO9ulpQ.css">
```

---

## Что сделать

**Файл:** `packages/web/ai_mini_box_web/server.py` (строки 74-86)

### 1. Заменить mount корня на mount `/assets`

```python
# Было:
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

# Стало:
static_dir = Path(__file__).parent / "static"
assets_dir = static_dir / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
```

### 2. Переписать `serve_spa()` — добавить отдачу корневых статик-файлов

```python
@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404)
    # Serve root-level static files (favicon.svg, icons.svg)
    file_path = static_dir / full_path
    if file_path.is_file():
        media_type, _ = mimetypes.guess_type(str(file_path))
        return Response(file_path.read_bytes(), media_type=media_type or "application/octet-stream")
    # SPA fallback — serve index.html for all non-API routes
    html_path = static_dir / "index.html"
    if html_path.exists():
        return Response(html_path.read_text(encoding="utf-8"), media_type="text/html")
    raise HTTPException(status_code=404)
```

**Потребуется импорт:** `import mimetypes` (добавить в начало файла).

### 3. Удалить больше не нужные импорты

Если после замены не используются: `from fastapi.responses import Response` — нужен. `from pathlib import Path` — нужен.

---

## Проверка

| # | Путь | Ожидаемый результат | Кто отвечает |
|---|---|---|---|
| 1 | `/` | `index.html` → SPA загружается | Mount / assets + serve_spa |
| 2 | `/plugins/llm` | `index.html` → SPA → PluginDetail | serve_spa fallback |
| 3 | `/plugins` (TODO) | `index.html` → SPA → Plugins | serve_spa fallback |
| 4 | `/calendar` | `index.html` → SPA → Calendar | serve_spa fallback |
| 5 | `/assets/index-CaeyohaM.js` | JS-бандл | StaticFiles mount |
| 6 | `/assets/index-DEO9ulpQ.css` | CSS-бандл | StaticFiles mount |
| 7 | `/favicon.svg` | SVG-файл | serve_spa file check |
| 8 | `/icons.svg` | SVG-файл | serve_spa file check |
| 9 | `/api/health` | `{"status":"ok"}` | API router |
| 10 | `/api/llm/health` | JSON health | API router |
| 11 | `/api/nonexistent` | 404 JSON | serve_spa → api/ check |
| 12 | `/favicon.ico` | 404 (браузер сам запрашивает) | serve_spa → файла нет → 404 |

**Критично:** `console` вкладка браузера — никаких `Failed to load resource` 404.

---

## Acceptance criteria

- Все SPA-роуты (`/plugins/:name`, `/messages/:id`, `/contacts/:id`, `/calendar` и т.д.) отдают `index.html` и корректно рендерят компонент
- JS/CSS-бандлы загружаются без ошибок (200)
- `/favicon.svg` отдаётся с корректным Content-Type
- API-роуты не затронуты
- Браузерная консоль без 404
- Статические файлы (favicon, icons) доступны по прямым ссылкам

---

## Scope exclude

- Не менять API-роутеры
- Не менять фронтенд (App.tsx, компоненты)
- Не менять конфиг сборки (vite.config.ts)
- Не пересобирать фронтенд
