import asyncio
import mimetypes
import os
import signal
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from loguru import logger

from ai_mini_box_web.routers import analytics, business, contacts, email, help, knowledge_base, llm_folders, messages, order_items, orders, plugins, products, tasks, templates
from ai_mini_box_web.routers.llm_folders import message_categories_router
from ai_mini_box_web.services.update_checker import warn_updates

_reload_requested = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    warn_updates("ai-mini-box-core", "ai-mini-box-web")
    if not os.environ.get("AI_BOX_SECRET"):
        logger.warning(
            "AI_BOX_SECRET not set — using default encryption key. "
            "Set AI_BOX_SECRET environment variable for production."
        )
    loop = asyncio.get_event_loop()

    def _handle_reload(signum, frame):
        global _reload_requested
        _reload_requested = True
        logger.info("Reload signal received, shutting down...")

    signal.signal(signal.SIGTERM, _handle_reload)
    signal.signal(signal.SIGINT, _handle_reload)

    yield

    if _reload_requested:
        logger.info("Graceful shutdown complete, proceeding with reload")


app = FastAPI(title="AI mini box", version="5.0.1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "5.0.1"}


app.include_router(contacts.router, prefix="/api/contacts", tags=["contacts"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(order_items.router, prefix="/api/orders", tags=["orders"])
app.include_router(plugins.router, prefix="/api/plugins", tags=["plugins"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(knowledge_base.router, prefix="/api/knowledge-base", tags=["knowledge-base"])
app.include_router(llm_folders.router, prefix="/api/llm", tags=["llm"])
app.include_router(message_categories_router, tags=["llm"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(email.router, prefix="/api/email", tags=["email"])
app.include_router(help.router)
app.include_router(business.router, prefix="/api/business", tags=["business"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["templates"])

static_dir = Path(__file__).parent / "static"
assets_dir = static_dir / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404)
    file_path = (static_dir / full_path).resolve()
    if not str(file_path).startswith(str(static_dir.resolve())):
        raise HTTPException(status_code=403)
    if file_path.is_file():
        media_type, _ = mimetypes.guess_type(str(file_path))
        return Response(file_path.read_bytes(), media_type=media_type or "application/octet-stream")
    if not hasattr(serve_spa, "_cached_html"):
        html_path = static_dir / "index.html"
        if html_path.exists():
            serve_spa._cached_html = html_path.read_text(encoding="utf-8")
    if hasattr(serve_spa, "_cached_html"):
        return Response(serve_spa._cached_html, media_type="text/html")
    raise HTTPException(status_code=404)
