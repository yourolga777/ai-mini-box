import importlib.metadata
from pathlib import Path


class PluginManager:
    def __init__(self):
        self._log_dir = Path("logs")
        self._log_dir.mkdir(parents=True, exist_ok=True)

    def list_plugins(self) -> list[dict]:
        plugins = []
        for ep in importlib.metadata.entry_points(group="ai_mini_box.tools"):
            module = ep.module if hasattr(ep, "module") else ep.value
            plugins.append({
                "name": ep.name,
                "module": ep.value,
                "status": "stopped",
                "pid": None,
            })
        return plugins

    def get_plugin(self, name: str) -> dict | None:
        for ep in importlib.metadata.entry_points(group="ai_mini_box.tools"):
            if ep.name == name:
                return {
                    "name": ep.name,
                    "module": ep.value,
                    "status": "stopped",
                    "pid": None,
                }
        return None

    def get_logs(self, name: str, max_lines: int = 100) -> list[str]:
        log_file = self._log_dir / f"plugin_{name}.log"
        if not log_file.exists():
            return []
        lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[-max_lines:]
