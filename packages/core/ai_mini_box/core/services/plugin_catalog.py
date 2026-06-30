import importlib.metadata
import json
from pathlib import Path
from typing import Any

from packaging.version import Version


class PluginCatalog:
    BUILTIN_PATH = Path(__file__).parent.parent.parent / "data" / "plugin-catalog.json"

    def __init__(self, data_dir: str | Path = "data"):
        self._data_dir = Path(data_dir)

    def load_builtin(self) -> list[dict[str, Any]]:
        if not self.BUILTIN_PATH.exists():
            return []
        with open(self.BUILTIN_PATH, encoding="utf-8") as f:
            return json.load(f)

    def _cached_path(self) -> Path:
        return self._data_dir / "plugin-catalog.json"

    def _read_json(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _write_json(self, path: Path, data: list[dict[str, Any]]):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self) -> list[dict[str, Any]]:
        cached = self._cached_path()
        if cached.exists():
            return self._read_json(cached)
        return self.load_builtin()

    def sync(self):
        builtin = self.load_builtin()
        cached = self._cached_path()

        if cached.exists():
            existing = self._read_json(cached)
            names = {e["name"] for e in builtin}
            merged = list(builtin)
            for entry in existing:
                if entry["name"] not in names:
                    merged.append(entry)
            self._write_json(cached, merged)
        else:
            self._write_json(cached, builtin)

    def get_installed(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for ep in importlib.metadata.entry_points(group="ai_mini_box.tools"):
            try:
                dist = importlib.metadata.distribution(ep.value.partition("=")[0].strip())
                result[ep.name] = dist.version
            except (importlib.metadata.PackageNotFoundError, Exception):
                result[ep.name] = "0.0.0"
        return result

    def get_status(self) -> list[dict[str, Any]]:
        catalog = self.load()
        installed = self.get_installed()

        for entry in catalog:
            entry["installed"] = entry["name"] in installed
            entry["installed_version"] = installed.get(entry["name"], None)
            if entry["installed"] and entry.get("version"):
                try:
                    entry["has_update"] = Version(entry["version"]) > Version(entry["installed_version"])
                except Exception:
                    entry["has_update"] = False
            else:
                entry["has_update"] = False
        return catalog
