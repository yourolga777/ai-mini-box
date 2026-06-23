import asyncio
import signal
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from loguru import logger

from ai_mini_box_web.routers import contacts, help, messages, orders, plugins, products
from ai_mini_box_web.services.update_checker import warn_updates

_reload_requested = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    warn_updates("ai-mini-box-core", "ai-mini-box-web")
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


app = FastAPI(title="AI mini box", version="0.1.1", lifespan=lifespan)

app.include_router(contacts.router, prefix="/api/contacts", tags=["contacts"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(plugins.router, prefix="/api/plugins", tags=["plugins"])
app.include_router(help.router)

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
