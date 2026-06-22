def test_list_contacts(client):
    resp = client.get("/api/contacts/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_contact(client):
    resp = client.post("/api/contacts/", json={"name": "Alice", "phone": "+123"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Alice"
    assert data["id"] is not None


def test_get_contact(client):
    created = client.post("/api/contacts/", json={"name": "Bob"}).json()
    resp = client.get(f"/api/contacts/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Bob"


def test_get_contact_not_found(client):
    resp = client.get("/api/contacts/999")
    assert resp.status_code == 404


def test_update_contact(client):
    created = client.post("/api/contacts/", json={"name": "Charlie"}).json()
    resp = client.put(f"/api/contacts/{created['id']}", json={"name": "Chuck"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Chuck"


def test_delete_contact(client):
    created = client.post("/api/contacts/", json={"name": "Dave"}).json()
    resp = client.delete(f"/api/contacts/{created['id']}")
    assert resp.status_code == 204
    resp = client.get(f"/api/contacts/{created['id']}")
    assert resp.status_code == 404


def test_search_contacts(client):
    client.post("/api/contacts/", json={"name": "Alice Wonderland"})
    client.post("/api/contacts/", json={"name": "Bob The Builder"})
    resp = client.get("/api/contacts/?search=Alice")
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Alice Wonderland"
