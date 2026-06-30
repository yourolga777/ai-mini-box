import os
import subprocess
import sys
from pathlib import Path

import pytest

from ai_mini_box_web.services.plugin_manager import PluginManager


class TestDaemonLifecycle:
    def test_start_daemon_uses_stdin_devnull(self, mocker):
        """Daemon subprocess must not inherit stdin from parent."""
        mock_proc = mocker.Mock()
        mock_proc.pid = 12345
        mock_popen = mocker.patch("subprocess.Popen", return_value=mock_proc)
        mocker.patch("ai_mini_box_web.services.plugin_manager.PluginManager._is_running", return_value=False)

        pm = PluginManager()
        result = pm.start_daemon("telegram")

        assert result["success"] is True
        assert result["pid"] == 12345

        call_kwargs = mock_popen.call_args[1]
        assert call_kwargs["stdin"] == subprocess.DEVNULL

    def test_start_daemon_uses_correct_command(self, mocker):
        """Must run: sys.executable -m ai_mini_box <name> daemon."""
        mock_proc = mocker.Mock()
        mock_proc.pid = 12345
        mock_popen = mocker.patch("subprocess.Popen", return_value=mock_proc)
        mocker.patch("ai_mini_box_web.services.plugin_manager.PluginManager._is_running", return_value=False)

        pm = PluginManager()
        pm.start_daemon("telegram")

        call_args = mock_popen.call_args[0][0]
        assert call_args == [sys.executable, "-m", "ai_mini_box", "telegram", "daemon"]

    def test_start_daemon_redirects_stdout_to_log(self, mocker, tmp_path):
        """stdout must be written to logs/plugin_<name>.log."""
        mock_proc = mocker.Mock()
        mock_proc.pid = 12345
        mock_popen = mocker.patch("subprocess.Popen", return_value=mock_proc)
        mocker.patch("ai_mini_box_web.services.plugin_manager.PluginManager._is_running", return_value=False)

        pm = PluginManager()
        mocker.patch.object(pm, "_log_dir", tmp_path)
        pm.start_daemon("telegram")

        call_kwargs = mock_popen.call_args[1]
        stdout_file = call_kwargs["stdout"]
        assert stdout_file.mode == "a"

    def test_start_daemon_rejects_already_running(self, mocker):
        mock_popen = mocker.patch("subprocess.Popen")
        pm = PluginManager()

        pm._daemon_pids["telegram"] = 99999
        mocker.patch.object(pm, "_is_running", return_value=True)

        result = pm.start_daemon("telegram")
        assert result["success"] is False
        assert "already running" in result["output"]
        mock_popen.assert_not_called()

    def test_start_daemon_handles_popen_failure(self, mocker):
        mocker.patch("subprocess.Popen", side_effect=OSError("fork failed"))
        mocker.patch("ai_mini_box_web.services.plugin_manager.PluginManager._is_running", return_value=False)

        pm = PluginManager()
        result = pm.start_daemon("telegram")
        assert result["success"] is False
        assert "fork failed" in result["output"]

    def test_stop_daemon_returns_error_when_not_running(self, mocker):
        pm = PluginManager()
        result = pm.stop_daemon("nonexistent")
        assert result["success"] is False

    def test_stop_daemon_success(self, mocker):
        pm = PluginManager()
        pm._daemon_pids["telegram"] = 12345

        mocker.patch.object(pm, "_is_running", return_value=True)
        if sys.platform == "win32":
            mocker.patch("subprocess.run", return_value=mocker.Mock(returncode=0))
        else:
            mocker.patch("os.kill")
            mocker.patch("time.sleep")

        result = pm.stop_daemon("telegram")
        assert result["success"] is True

    def test_stop_daemon_handles_already_exited(self, mocker):
        pm = PluginManager()
        pm._daemon_pids["telegram"] = 12345
        mocker.patch.object(pm, "_is_running", return_value=False)

        result = pm.stop_daemon("telegram")
        assert result["success"] is False
        assert "already exited" in result["output"]

    def test_daemon_pid_persistence(self, mocker, tmp_path):
        """PID must be saved to and loaded from data/daemon_pids.json."""
        mock_proc = mocker.Mock()
        mock_proc.pid = 12345
        mocker.patch("subprocess.Popen", return_value=mock_proc)
        mocker.patch("ai_mini_box_web.services.plugin_manager.PluginManager._is_running", return_value=False)
        pids_path = tmp_path / "daemon_pids.json"
        mocker.patch.object(PluginManager, "_daemon_pids_path", lambda self: pids_path)

        pm = PluginManager()
        pm.start_daemon("telegram")

        assert pids_path.exists()
        import json
        data = json.loads(pids_path.read_text(encoding="utf-8"))
        assert data["telegram"] == 12345

        pm2 = PluginManager()
        assert pm2._daemon_pids.get("telegram") == 12345

    def test_is_running_on_windows_uses_tasklist(self, mocker):
        if sys.platform != "win32":
            pytest.skip("Windows-specific test")

        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value.stdout = "python.exe   12345 Console  ... running"

        pm = PluginManager()
        result = pm._is_running(12345)
        assert result is True
        assert "tasklist" in mock_run.call_args[0][0]

    def test_is_running_returns_false_when_pid_not_found(self, mocker):
        if sys.platform != "win32":
            pytest.skip("Windows-specific test")

        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value.stdout = ""

        pm = PluginManager()
        result = pm._is_running(99999)
        assert result is False

    def test_list_plugins_shows_running_status(self, mocker):
        mock_entry = mocker.Mock()
        mock_entry.name = "demo"
        mock_entry.value = "test:register"

        mocker.patch(
            "importlib.metadata.entry_points",
            return_value=[mock_entry],
        )

        pm = PluginManager()
        pm._daemon_pids["demo"] = 12345
        mocker.patch.object(pm, "_is_running", return_value=True)

        plugins = pm.list_plugins()
        demo = [p for p in plugins if p["name"] == "demo"][0]
        assert demo["status"] == "running"
        assert demo["pid"] == 12345
