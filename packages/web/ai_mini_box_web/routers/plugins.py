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


@router.get("")
def list_plugins():
    return _manager.list_plugins()


@router.get("/{name}")
def get_plugin(name: str):
    plugin = _manager.get_plugin(name)
    if plugin is None:
        raise HTTPException(404, detail=f"Plugin '{name}' not found")
    return plugin


@router.get("/check/package")
def check_package(package: str):
    if not PACKAGE_RE.match(package):
        raise HTTPException(400, detail=f"Invalid package name. Must match ai-mini-box-* or ai_mini_box_*")
    return {"installed": _manager.check_installed(package)}


@router.post("/install")
async def install_pypi(body: InstallRequest, request: Request):
    package = body.package.strip()
    if not PACKAGE_RE.match(package):
        raise HTTPException(400, detail="Only ai-mini-box-* packages can be installed")
    if _manager.check_installed(package):
        raise HTTPException(409, detail=f"Package '{package}' is already installed")

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _manager.install_from_pypi, package)

    logger_kw = dict(pkg=package, source="pypi", ip=request.client.host, success=result["success"])
    logger_kw["output"] = result["output"][:500]
    from loguru import logger
    logger.info("Plugin install | pkg={pkg} source={source} ip={ip} success={success}", **logger_kw)

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


@router.post("/{name}/start", status_code=501)
def start_plugin(name: str):
    return {"detail": "Plugin lifecycle management not yet implemented"}


@router.post("/{name}/stop", status_code=501)
def stop_plugin(name: str):
    return {"detail": "Plugin lifecycle management not yet implemented"}


@router.get("/{name}/logs")
def get_plugin_logs(name: str):
    lines = _manager.get_logs(name)
    return {"plugin": name, "lines": lines}


async def _delayed_reload():
    await asyncio.sleep(2)
    from loguru import logger
    logger.info("Reloading server to activate new plugin...")
    os.execv(sys.executable, [sys.executable, "-m", "ai_mini_box", "web"] + sys.argv[1:])
