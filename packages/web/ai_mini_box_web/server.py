from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from ai_mini_box_web.routers import contacts, messages, orders, plugins, products


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="AI mini box", version="0.1.0", lifespan=lifespan)

app.include_router(contacts.router, prefix="/api/contacts", tags=["contacts"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(plugins.router, prefix="/api/plugins", tags=["plugins"])

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
