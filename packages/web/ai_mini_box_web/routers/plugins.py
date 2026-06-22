import importlib.metadata

from fastapi import APIRouter

from ai_mini_box_web.services.plugin_manager import PluginManager

router = APIRouter()

_manager = PluginManager()


@router.get("/")
def list_plugins():
    return _manager.list_plugins()


@router.get("/{name}")
def get_plugin(name: str):
    plugin = _manager.get_plugin(name)
    if plugin is None:
        from fastapi import HTTPException
        raise HTTPException(404, detail=f"Plugin '{name}' not found")
    return plugin


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
