import pytest


def test_list_plugins(client):
    resp = client.get("/api/plugins")
    assert resp.status_code == 200
    plugins = resp.json()
    assert isinstance(plugins, list)


def test_get_plugin_existing(client):
    resp = client.get("/api/plugins")
    plugins = resp.json()
    if plugins:
        name = plugins[0]["name"]
        resp = client.get(f"/api/plugins/{name}")
        assert resp.status_code == 200
        assert resp.json()["name"] == name


def test_get_plugin_not_found(client):
    resp = client.get("/api/plugins/nonexistent")
    assert resp.status_code == 404


def test_start_plugin_returns_501(client):
    resp = client.post("/api/plugins/demo/start")
    assert resp.status_code == 501


def test_stop_plugin_returns_501(client):
    resp = client.post("/api/plugins/demo/stop")
    assert resp.status_code == 501


def test_get_plugin_logs_empty(client):
    resp = client.get("/api/plugins/demo/logs")
    assert resp.status_code == 200
    assert resp.json()["lines"] == []


class TestCheckPackage:
    def test_check_unknown_package(self, client):
        resp = client.get("/api/plugins/check/package?package=ai-mini-box-nonexistent")
        assert resp.status_code == 200
        assert resp.json()["installed"] is False

    def test_check_invalid_package_name(self, client):
        resp = client.get("/api/plugins/check/package?package=requests")
        assert resp.status_code == 400

    def test_check_valid_name_format(self, client):
        resp = client.get("/api/plugins/check/package?package=ai-mini-box-telegram")
        assert resp.status_code == 200


class TestInstallPypi:
    def test_install_success(self, client, monkeypatch):
        monkeypatch.setattr(
            "ai_mini_box_web.services.plugin_manager.PluginManager.check_installed",
            lambda self, pkg: False,
        )
        monkeypatch.setattr(
            "ai_mini_box_web.services.plugin_manager.PluginManager.install_from_pypi",
            lambda self, pkg: {"success": True, "output": "Installed"},
        )
        resp = client.post("/api/plugins/install", json={"package": "ai-mini-box-telegram"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["reload"] is True

    def test_install_already_installed(self, client, monkeypatch):
        monkeypatch.setattr(
            "ai_mini_box_web.services.plugin_manager.PluginManager.check_installed",
            lambda self, pkg: True,
        )
        resp = client.post("/api/plugins/install", json={"package": "ai-mini-box-telegram"})
        assert resp.status_code == 409

    def test_install_invalid_package_name(self, client):
        resp = client.post("/api/plugins/install", json={"package": "requests"})
        assert resp.status_code == 400

    def test_install_failure(self, client, monkeypatch):
        monkeypatch.setattr(
            "ai_mini_box_web.services.plugin_manager.PluginManager.check_installed",
            lambda self, pkg: False,
        )
        monkeypatch.setattr(
            "ai_mini_box_web.services.plugin_manager.PluginManager.install_from_pypi",
            lambda self, pkg: {"success": False, "output": "Error: not found"},
        )
        resp = client.post("/api/plugins/install", json={"package": "ai-mini-box-telegram"})
        assert resp.status_code == 200
        assert resp.json()["success"] is False


class TestInstallUpload:
    def test_upload_invalid_extension(self, client):
        resp = client.post("/api/plugins/install/upload", files={"file": ("bad.txt", b"not a wheel", "text/plain")})
        assert resp.status_code == 400

    def test_upload_success(self, client, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "ai_mini_box_web.services.plugin_manager.PluginManager.check_installed",
            lambda self, pkg: False,
        )
        monkeypatch.setattr(
            "ai_mini_box_web.services.plugin_manager.PluginManager.install_from_wheel",
            lambda self, path: {"success": True, "output": "Installed from wheel"},
        )
        resp = client.post(
            "/api/plugins/install/upload",
            files={"file": ("plugin-0.1.0-py3-none-any.whl", b"fake wheel content", "application/octet-stream")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["reload"] is True


class TestUninstall:
    def test_uninstall_protected_plugin(self, client):
        resp = client.delete("/api/plugins/core")
        assert resp.status_code == 403

    def test_uninstall_not_in_entry_points(self, client):
        resp = client.delete("/api/plugins/nonexistent-plugin")
        assert resp.status_code == 404

    def test_uninstall_not_found(self, client):
        resp = client.delete("/api/plugins/nonexistent-plugin-12345")
        assert resp.status_code == 404

    def test_uninstall_success(self, client, monkeypatch):
        monkeypatch.setattr(
            "ai_mini_box_web.services.plugin_manager.PluginManager.get_plugin",
            lambda self, name: {"name": name, "module": "test", "status": "installed", "pid": None},
        )
        monkeypatch.setattr(
            "ai_mini_box_web.services.plugin_manager.PluginManager.uninstall",
            lambda self, pkg: {"success": True, "output": "Uninstalled"},
        )
        resp = client.delete("/api/plugins/telegram")
        assert resp.status_code == 200
        assert resp.json()["success"] is True
