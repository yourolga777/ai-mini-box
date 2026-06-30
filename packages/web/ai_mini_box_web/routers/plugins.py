import asyncio
import importlib.metadata
import os
import sys
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from pydantic import BaseModel

from ai_mini_box.core.services.plugin_catalog import PluginCatalog
from ai_mini_box_web.services.plugin_manager import (
    PACKAGE_RE,
    PROTECTED_PLUGINS,
    PluginManager,
)

router = APIRouter()

_manager = PluginManager()
_catalog = PluginCatalog()

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


# --- catalog ---

@router.get("/catalog")
def list_catalog():
    return _catalog.get_status()

# --- plugin CRUD ---

@router.get("")
def list_plugins():
    plugins = _manager.list_plugins()
    catalog_map = {e["name"]: e for e in _catalog.get_status()}
    for p in plugins:
        entry = catalog_map.get(p["name"])
        p["description"] = entry.get("description", "") if entry else ""
        p["version"] = entry.get("version") if entry else None
        p["installed_version"] = None
        p["has_update"] = False
        if entry and entry.get("package"):
            try:
                pkg = entry["package"]
                p["installed_version"] = importlib.metadata.version(pkg)
            except (importlib.metadata.PackageNotFoundError, Exception):
                p["installed_version"] = None
            if p["installed_version"] and entry.get("version"):
                p["has_update"] = p["installed_version"] != entry["version"]
    return plugins


@router.get("/check/package")
def check_package(package: str):
    if not PACKAGE_RE.match(package):
        raise HTTPException(400, detail="Invalid package name. Must match ai-mini-box-* or ai_mini_box_*")
    return {"installed": _manager.check_installed(package)}


@router.get("/{name}/config-schema")
def get_plugin_config_schema(name: str):
    try:
        from ai_mini_box.core.services.config_provider import get_config_provider
        provider = get_config_provider(name)
        if provider is not None:
            return provider.get_schema()
    except Exception:
        pass
    plugin = _manager.get_plugin(name)
    if plugin is None:
        raise HTTPException(404, detail=f"Plugin '{name}' not found")
    try:
        module_path = plugin["module"].split(":")[0]
        mod = importlib.import_module(module_path)
        if not hasattr(mod, "config_schema"):
            raise HTTPException(404, detail=f"Plugin '{name}' does not expose a config schema")
        return mod.config_schema()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=f"Error loading config schema: {e}")


@router.get("/{name}/config")
def get_plugin_config(name: str):
    cfg = _manager.get_plugin_config(name)
    if cfg is None:
        raise HTTPException(404, detail=f"No config found for plugin '{name}'")
    return cfg


@router.post("/{name}/config")
def set_plugin_config(name: str, body: dict):
    result = _manager.set_plugin_config(name, body)
    if not result["success"]:
        raise HTTPException(400, detail=result.get("error", "Unknown error"))
    return result


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


@router.post("/{name}/update")
def update_plugin(name: str):
    if not _manager.get_plugin(name):
        raise HTTPException(404, detail=f"Plugin '{name}' not found")
    return _manager.update_plugin(name)


@router.post("/{name}/stop")
def stop_plugin_daemon(name: str):
    result = _manager.stop_daemon(name)
    if not result["success"] and "not running" in result["output"]:
        raise HTTPException(404, detail=result["output"])
    return result


@router.post("/{name}/verify-token")
def verify_token(name: str):
    if name != "telegram":
        raise HTTPException(400, detail="Only telegram plugin supports token verification")

    from ai_mini_box.core.services.registry import get_service

    svc = get_service("telegram")
    if svc is None:
        raise HTTPException(502, detail="Telegram service not available")

    try:
        me = svc.verify_token()
    except Exception as e:
        raise HTTPException(502, detail=f"Telegram API error: {e}")

    bot_name: str = me.get("first_name", "")
    bot_username: str = me.get("username", "")

    if bot_name:
        _manager.set_config("telegram_bot_name", bot_name)
    if bot_username:
        _manager.set_config("telegram_bot_username", bot_username)

    return {"success": True, "bot_name": bot_name, "bot_username": bot_username}


@router.post("/{name}/action")
def plugin_action(name: str, body: ActionRequest):
    if name == "telegram" and body.action == "poll":
        from ai_mini_box.core.services.registry import get_service

        svc = get_service("telegram")
        if svc is None:
            raise HTTPException(502, detail="Telegram service not available")
        result = svc.poll()
        if not result.get("success"):
            raise HTTPException(502, detail=result.get("error", "Poll failed"))
        result["output"] = f"Обработано {result.get('count', 0)} новых сообщений"
        return result
    raise HTTPException(400, detail=f"Unknown action '{body.action}' for plugin '{name}'")


@router.get("/{name}/logs")
def get_plugin_logs(name: str):
    lines = _manager.get_logs(name)
    return {"plugin": name, "lines": lines}


async def _delayed_reload():
    await asyncio.sleep(2)
    from loguru import logger
    logger.info("Reloading server to activate new plugin...")
    os.execv(sys.executable, [sys.executable, "-m", "ai_mini_box", "web"] + sys.argv[1:])
