import asyncio
import os
import sys
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from pydantic import BaseModel

from ai_mini_box_web.services.plugin_manager import (
    PACKAGE_RE,
    PROTECTED_PLUGINS,
    PluginManager,
)

router = APIRouter()

_manager = PluginManager()

_UPLOAD_DIR = Path("data/uploads")


class InstallRequest(BaseModel):
    package: str


class ActionRequest(BaseModel):
    action: str


class ConfigSetRequest(BaseModel):
    key: str
    value: str


# --- config (must be before /{name} to avoid path param conflict) ---

@router.get("/config")
def get_config():
    return _manager.get_config()


@router.post("/config/set")
def set_config(body: ConfigSetRequest):
    result = _manager.set_config(body.key, body.value)
    if not result["success"]:
        raise HTTPException(400, detail=result.get("error", "Unknown error"))
    return result


# --- plugin CRUD ---

@router.get("")
def list_plugins():
    return _manager.list_plugins()


@router.get("/check/package")
def check_package(package: str):
    if not PACKAGE_RE.match(package):
        raise HTTPException(400, detail="Invalid package name. Must match ai-mini-box-* or ai_mini_box_*")
    return {"installed": _manager.check_installed(package)}


@router.get("/{name}")
def get_plugin(name: str):
    plugin = _manager.get_plugin(name)
    if plugin is None:
        raise HTTPException(404, detail=f"Plugin '{name}' not found")
    return plugin


@router.post("/install")
async def install_pypi(body: InstallRequest, request: Request):
    package = body.package.strip()
    if not PACKAGE_RE.match(package):
        raise HTTPException(400, detail="Only ai-mini-box-* packages can be installed")
    if _manager.check_installed(package):
        raise HTTPException(409, detail=f"Package '{package}' is already installed")

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _manager.install_from_pypi, package)

    from loguru import logger
    logger.info("Plugin install | pkg={} source={} ip={} success={}",
                package, "pypi", request.client.host, result["success"])

    if result["success"]:
        asyncio.create_task(_delayed_reload())
        return {**result, "reload": True}
    return result


@router.post("/install/upload")
async def install_upload(file: UploadFile = File(...), request: Request = None):
    if not file.filename or not file.filename.endswith(".whl"):
        raise HTTPException(400, detail="Only .whl files are accepted")

    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4()}_{file.filename}"
    dest = _UPLOAD_DIR / unique_name
    dest.write_bytes(await file.read())

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _manager.install_from_wheel, dest)

    client_ip = request.client.host if request else "unknown"
    from loguru import logger
    logger.info("Plugin install | pkg={} source={} ip={} success={}",
                file.filename, "upload", client_ip, result["success"])

    if result["success"]:
        asyncio.create_task(_delayed_reload())
        return {**result, "reload": True}
    return result


@router.delete("/{name}")
def uninstall_plugin(name: str, request: Request = None):
    if name in PROTECTED_PLUGINS:
        raise HTTPException(403, detail=f"Cannot uninstall protected plugin '{name}'")
    if not _manager.get_plugin(name):
        raise HTTPException(404, detail=f"Plugin '{name}' not found")

    pip_name = f"ai-mini-box-{name}"
    result = _manager.uninstall(pip_name)

    client_ip = request.client.host if request else "unknown"
    from loguru import logger
    logger.info("Plugin uninstall | pkg={} ip={} success={}", pip_name, client_ip, result["success"])

    return result


@router.post("/{name}/start")
def start_plugin_daemon(name: str):
    plugin = _manager.get_plugin(name)
    if not plugin:
        raise HTTPException(404, detail=f"Plugin '{name}' not found")

    result = _manager.start_daemon(name)
    if not result["success"]:
        raise HTTPException(409, detail=result["output"])
    return result


@router.post("/{name}/stop")
def stop_plugin_daemon(name: str):
    result = _manager.stop_daemon(name)
    if not result["success"] and "not running" in result["output"]:
        raise HTTPException(404, detail=result["output"])
    return result


@router.post("/{name}/action")
def plugin_action(name: str, body: ActionRequest):
    if name == "telegram" and body.action == "poll":
        return _run_poll()
    raise HTTPException(400, detail=f"Unknown action '{body.action}' for plugin '{name}'")


@router.get("/{name}/logs")
def get_plugin_logs(name: str):
    lines = _manager.get_logs(name)
    return {"plugin": name, "lines": lines}


# --- internal ---

def _run_poll():
    token, allowed, interval = _resolve_telegram_config()
    if not token:
        raise HTTPException(400, detail="telegram_token not set")

    from ai_mini_box_telegram.bot import TelegramBot
    from ai_mini_box_telegram.handlers import process_update
    from ai_mini_box_telegram.state import FileTelegramStateRepo
    from ai_mini_box.infrastructure.database import get_db

    bot = TelegramBot(token)
    state = FileTelegramStateRepo()
    offset = state.get_offset()
    try:
        updates = bot.get_updates(offset=offset)
    except Exception as e:
        raise HTTPException(502, detail=f"Telegram API error: {e}")

    count = 0
    for update in updates:
        with get_db() as session:
            if process_update(update, session, allowed_chat_ids=allowed):
                count += 1
                state.save_offset(update["update_id"] + 1)

    return {"success": True, "count": count, "output": f"Processed {count} new messages"}


def _resolve_telegram_config() -> tuple:
    config = _manager.get_config()
    token = config.get("telegram_token", "")
    allowed = config.get("telegram_allowed_chat_ids", [])
    interval = config.get("poll_interval", 30)
    return token, allowed, interval


async def _delayed_reload():
    await asyncio.sleep(2)
    from loguru import logger
    logger.info("Reloading server to activate new plugin...")
    os.execv(sys.executable, [sys.executable, "-m", "ai_mini_box", "web"] + sys.argv[1:])
