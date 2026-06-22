def test_list_plugins(client):
    resp = client.get("/api/plugins/")
    assert resp.status_code == 200
    plugins = resp.json()
    assert isinstance(plugins, list)


def test_get_plugin_existing(client):
    resp = client.get("/api/plugins/")
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
