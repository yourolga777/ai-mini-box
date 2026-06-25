import importlib.metadata
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

from loguru import logger

from ai_mini_box.infrastructure.config import JsonConfigManager, SENSITIVE_FIELDS

PACKAGE_RE = re.compile(r"^ai[-_]mini[-_]box[-_]", re.IGNORECASE)
PROTECTED_PLUGINS = frozenset({"core", "web"})


class PluginManager:
    def __init__(self):
        self._log_dir = Path("logs")
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._daemon_pids: dict[str, int] = {}
        self._load_daemon_pids()

    # --- discovery ---

    def list_plugins(self) -> list[dict]:
        plugins = []
        for ep in importlib.metadata.entry_points(group="ai_mini_box.tools"):
            plugins.append(self._plugin_info(ep))
        return plugins

    def get_plugin(self, name: str) -> dict | None:
        for ep in importlib.metadata.entry_points(group="ai_mini_box.tools"):
            if ep.name == name:
                return self._plugin_info(ep)
        return None

    def _plugin_info(self, ep) -> dict:
        pid = self._daemon_pids.get(ep.name)
        return {
            "name": ep.name,
            "module": ep.value,
            "status": "running" if pid and self._is_running(pid) else "installed",
            "pid": pid,
        }

    # --- logs ---

    def get_logs(self, name: str, max_lines: int = 100) -> list[str]:
        log_file = self._log_dir / f"plugin_{name}.log"
        if not log_file.exists():
            return []
        lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[-max_lines:]

    # --- install / uninstall ---

    def check_installed(self, package: str) -> bool:
        try:
            importlib.metadata.distribution(package)
            return True
        except importlib.metadata.PackageNotFoundError:
            return False

    def install_from_pypi(self, package: str) -> dict:
        cmd = self._pip_install_args() + [package]
        logger.info("Running: {}", " ".join(cmd))
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "Installation timed out after 120 seconds"}
        except Exception as e:
            return {"success": False, "output": str(e)}
        self._invalidate()
        return {"success": result.returncode == 0, "output": result.stdout + result.stderr}

    def install_from_wheel(self, wheel_path: Path) -> dict:
        cmd = self._pip_install_args() + [str(wheel_path)]
        logger.info("Running: {}", " ".join(cmd))
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "Installation timed out after 120 seconds"}
        except Exception as e:
            return {"success": False, "output": str(e)}
        self._invalidate()
        return {"success": result.returncode == 0, "output": result.stdout + result.stderr}

    def uninstall(self, package: str) -> dict:
        cmd = [sys.executable, "-m", "pip", "uninstall", "-y", package]
        logger.info("Running: {}", " ".join(cmd))
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "Uninstall timed out after 60 seconds"}
        except Exception as e:
            return {"success": False, "output": str(e)}
        self._invalidate()
        return {"success": result.returncode == 0, "output": result.stdout + result.stderr}

    # --- daemon lifecycle ---

    def start_daemon(self, name: str) -> dict:
        if name in self._daemon_pids:
            pid = self._daemon_pids[name]
            if self._is_running(pid):
                return {"success": False, "output": f"Daemon already running (PID {pid})"}

        log_path = self._log_dir / f"plugin_{name}.log"
        cmd = [sys.executable, "-m", "ai_mini_box", name, "daemon"]

        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=open(log_path, "a", encoding="utf-8"),
                stderr=subprocess.STDOUT,
                startupinfo=startupinfo,
            )
        except Exception as e:
            return {"success": False, "output": str(e)}

        self._daemon_pids[name] = proc.pid
        self._save_daemon_pids()
        logger.info("Daemon started for {} (PID {})", name, proc.pid)
        return {"success": True, "output": f"Daemon started (PID {proc.pid})", "pid": proc.pid}

    def stop_daemon(self, name: str) -> dict:
        pid = self._daemon_pids.get(name)
        if not pid:
            return {"success": False, "output": "Daemon not running"}

        if not self._is_running(pid):
            del self._daemon_pids[name]
            self._save_daemon_pids()
            return {"success": False, "output": "Daemon process already exited"}

        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, timeout=5)
            else:
                os.kill(pid, signal.SIGTERM)
                time.sleep(2)
                if self._is_running(pid):
                    os.kill(pid, signal.SIGKILL)
        except Exception as e:
            return {"success": False, "output": str(e)}

        del self._daemon_pids[name]
        self._save_daemon_pids()
        logger.info("Daemon stopped for {} (PID {})", name, pid)
        return {"success": True, "output": f"Daemon stopped (PID {pid})"}

    # --- config ---

    def get_config(self) -> dict:
        config = JsonConfigManager().load()
        data = config.model_dump()
        for key in SENSITIVE_FIELDS:
            if key in data and data[key]:
                data[key] = "***"
        return data

    def set_config(self, key: str, value) -> dict:
        manager = JsonConfigManager()
        try:
            manager.set(key, value)
            return {"success": True}
        except (ValueError, Exception) as e:
            return {"success": False, "error": str(e)}

    # --- helpers ---

    def _is_running(self, pid: int) -> bool:
        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                    capture_output=True, text=True, timeout=5,
                )
                return str(pid) in result.stdout
            else:
                os.kill(pid, 0)
                return True
        except (OSError, subprocess.TimeoutExpired):
            return False

    def _pip_install_args(self) -> list[str]:
        base = [sys.executable, "-m", "pip", "install"]
        in_venv = hasattr(sys, "real_prefix") or sys.prefix != sys.base_prefix
        if not in_venv:
            base.append("--user")
        return base

    def _invalidate(self):
        importlib.invalidate_caches()

    def _daemon_pids_path(self) -> Path:
        return Path("data") / "daemon_pids.json"

    def _save_daemon_pids(self):
        path = self._daemon_pids_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._daemon_pids), encoding="utf-8")

    def _load_daemon_pids(self):
        path = self._daemon_pids_path()
        if path.exists():
            try:
                self._daemon_pids.update(json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, ValueError):
                self._daemon_pids = {}
