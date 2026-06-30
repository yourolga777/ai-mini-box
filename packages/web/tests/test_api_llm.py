import pytest
from fastapi import HTTPException

pytestmark = pytest.mark.usefixtures("db")

try:
    from ai_mini_box_llm.models import MessageCategory, MessageCategoryAssignment
    HAS_LLM = True
except ImportError:
    HAS_LLM = False


def _ensure_llm_tables():
    from ai_mini_box.infrastructure.database import Base, get_engine
    import ai_mini_box_llm.models  # noqa: F401
    Base.metadata.create_all(get_engine())


def _raise_502():
    raise HTTPException(502, detail="LLM plugin not installed")


class TestWithoutLLM:
    def test_list_folders_502(self, client, monkeypatch):
        monkeypatch.setattr(
            "ai_mini_box_web.routers.llm_folders._llm_models",
            _raise_502,
        )
        resp = client.get("/api/llm/folders")
        assert resp.status_code == 502

    def test_create_folders_502(self, client, monkeypatch):
        monkeypatch.setattr(
            "ai_mini_box_web.routers.llm_folders._llm_models",
            _raise_502,
        )
        resp = client.post("/api/llm/folders", json={"name": "Test"})
        assert resp.status_code == 502

    def test_process_502(self, client, monkeypatch):
        monkeypatch.setattr(
            "ai_mini_box.core.services.registry.get_service",
            lambda name: None,
        )
        resp = client.post("/api/llm/process")
        assert resp.status_code == 502

    def test_assign_all_502(self, client, monkeypatch):
        monkeypatch.setattr(
            "ai_mini_box.core.services.registry.get_service",
            lambda name: None,
        )
        resp = client.post("/api/llm/assign-all")
        assert resp.status_code == 502


@pytest.mark.skipif(not HAS_LLM, reason="LLM plugin not installed")
class TestFoldersCRUD:
    def test_list_folders_empty(self, client):
        _ensure_llm_tables()
        resp = client.get("/api/llm/folders")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_folder(self, client):
        _ensure_llm_tables()
        resp = client.post("/api/llm/folders", json={
            "name": "Тестовая",
            "description": "Описание",
            "color": "#2563eb",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Тестовая"
        assert data["color"] == "#2563eb"
        assert data["is_system"] is False
        assert data["message_count"] == 0

    def test_create_folder_invalid_color(self, client):
        _ensure_llm_tables()
        resp = client.post("/api/llm/folders", json={
            "name": "Bad color",
            "color": "#ffffff",
        })
        assert resp.status_code == 422

    def test_create_folder_duplicate(self, client):
        _ensure_llm_tables()
        client.post("/api/llm/folders", json={"name": "Test", "color": "#2563eb"})
        resp = client.post("/api/llm/folders", json={"name": "Test", "color": "#16a34a"})
        assert resp.status_code == 409

    def test_create_folder_empty_name(self, client):
        _ensure_llm_tables()
        resp = client.post("/api/llm/folders", json={"name": ""})
        assert resp.status_code == 422

    def test_update_folder(self, client):
        _ensure_llm_tables()
        created = client.post("/api/llm/folders", json={"name": "Old", "color": "#2563eb"}).json()
        resp = client.put(f"/api/llm/folders/{created['id']}", json={
            "name": "New name",
            "description": "Updated desc",
            "color": "#dc2626",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "New name"
        assert data["color"] == "#dc2626"

    def test_list_after_create(self, client):
        _ensure_llm_tables()
        client.post("/api/llm/folders", json={"name": "A", "color": "#2563eb"})
        client.post("/api/llm/folders", json={"name": "B", "color": "#16a34a"})
        resp = client.get("/api/llm/folders")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_delete_folder_not_found(self, client):
        _ensure_llm_tables()
        resp = client.delete("/api/llm/folders/999")
        assert resp.status_code == 404

    def test_delete_folder_move(self, client):
        _ensure_llm_tables()
        from ai_mini_box.core.container import RepoContainer
        from ai_mini_box.infrastructure.database import get_db as _get_db
        from ai_mini_box.core.models import Message

        created = client.post("/api/llm/folders", json={"name": "ToDel", "color": "#2563eb"}).json()
        folder_id = created["id"]

        with _get_db() as session:
            repos = RepoContainer(session)
            msg = repos.messages.add(Message(text="test", source="telegram"))
            mid = msg.id
            session.commit()
            client.post(f"/api/llm/folders/{folder_id}/assign", json={"message_id": mid})

        resp = client.delete(f"/api/llm/folders/{folder_id}?mode=move")
        assert resp.status_code == 200
        assert resp.json()["mode"] == "move"
        assert resp.json()["messages_affected"] == 1

    def test_assign_and_list_messages(self, client):
        _ensure_llm_tables()
        from ai_mini_box.core.container import RepoContainer
        from ai_mini_box.infrastructure.database import get_db as _get_db
        from ai_mini_box.core.models import Message

        folder = client.post("/api/llm/folders", json={"name": "AssignTest", "color": "#2563eb"}).json()

        with _get_db() as session:
            repos = RepoContainer(session)
            msg = repos.messages.add(Message(text="test assign", source="telegram"))
            mid = msg.id
            session.commit()

        resp = client.post(f"/api/llm/folders/{folder['id']}/assign", json={"message_id": mid})
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

        msgs = client.get(f"/api/llm/folders/{folder['id']}/messages").json()
        assert mid in msgs

    def test_unassign(self, client):
        _ensure_llm_tables()
        from ai_mini_box.core.container import RepoContainer
        from ai_mini_box.infrastructure.database import get_db as _get_db
        from ai_mini_box.core.models import Message

        folder = client.post("/api/llm/folders", json={"name": "UnassignTest", "color": "#2563eb"}).json()

        with _get_db() as session:
            repos = RepoContainer(session)
            msg = repos.messages.add(Message(text="test unassign", source="telegram"))
            mid = msg.id
            session.commit()

        client.post(f"/api/llm/folders/{folder['id']}/assign", json={"message_id": mid})
        resp = client.post(f"/api/llm/folders/{folder['id']}/unassign", json={"message_id": mid})
        assert resp.status_code == 200
        assert resp.json()["was_assigned"] is True

        msgs = client.get(f"/api/llm/folders/{folder['id']}/messages").json()
        assert mid not in msgs

    def test_assign_nonexistent_message(self, client):
        _ensure_llm_tables()
        folder = client.post("/api/llm/folders", json={"name": "Nonexist", "color": "#2563eb"}).json()
        resp = client.post(f"/api/llm/folders/{folder['id']}/assign", json={"message_id": 99999})
        assert resp.status_code == 404

    def test_delete_folder_with_messages(self, client):
        _ensure_llm_tables()
        from ai_mini_box.core.container import RepoContainer
        from ai_mini_box.infrastructure.database import get_db as _get_db
        from ai_mini_box.core.models import Message

        folder = client.post("/api/llm/folders", json={"name": "DelMsgs", "color": "#2563eb"}).json()

        with _get_db() as session:
            repos = RepoContainer(session)
            msg = repos.messages.add(Message(text="delete me", source="telegram"))
            mid = msg.id
            session.commit()

        client.post(f"/api/llm/folders/{folder['id']}/assign", json={"message_id": mid})

        resp = client.delete(f"/api/llm/folders/{folder['id']}?mode=delete_messages")
        assert resp.status_code == 200
        assert resp.json()["messages_affected"] == 1

        with _get_db() as session:
            repos = RepoContainer(session)
            assert repos.messages.get_by_id(mid) is None

    def test_message_count_in_list(self, client):
        _ensure_llm_tables()
        from ai_mini_box.core.container import RepoContainer
        from ai_mini_box.infrastructure.database import get_db as _get_db
        from ai_mini_box.core.models import Message

        folder = client.post("/api/llm/folders", json={"name": "CountTest", "color": "#2563eb"}).json()
        mids = []

        with _get_db() as session:
            repos = RepoContainer(session)
            for i in range(3):
                msg = repos.messages.add(Message(text=f"test {i}", source="telegram"))
                mids.append(msg.id)
            session.commit()

        for mid in mids:
            client.post(f"/api/llm/folders/{folder['id']}/assign", json={"message_id": mid})

        resp = client.get("/api/llm/folders")
        for f in resp.json():
            if f["id"] == folder["id"]:
                assert f["message_count"] == 3
                break
        else:
            pytest.fail("Folder not found in list")

    def test_update_system_folder_name_403(self, client):
        _ensure_llm_tables()
        MC, MCA = None, None
        try:
            from ai_mini_box_llm.models import MessageCategory, MessageCategoryAssignment
            MC, MCA = MessageCategory, MessageCategoryAssignment
        except ImportError:
            pytest.skip("LLM plugin not installed")
        from ai_mini_box.infrastructure.database import get_db as _get_db
        with _get_db() as session:
            cat = MC(name="SysFolder", color="#2563eb", is_system=True)
            session.add(cat)
            session.flush()
            session.refresh(cat)
            cid = cat.id
            session.commit()
        resp = client.put(f"/api/llm/folders/{cid}", json={"name": "Renamed"})
        assert resp.status_code == 403

    def test_delete_system_folder_403(self, client):
        _ensure_llm_tables()
        MC, MCA = None, None
        try:
            from ai_mini_box_llm.models import MessageCategory, MessageCategoryAssignment
            MC, MCA = MessageCategory, MessageCategoryAssignment
        except ImportError:
            pytest.skip("LLM plugin not installed")
        from ai_mini_box.infrastructure.database import get_db as _get_db
        with _get_db() as session:
            cat = MC(name="DelSys", color="#2563eb", is_system=True)
            session.add(cat)
            session.flush()
            session.refresh(cat)
            cid = cat.id
            session.commit()
        resp = client.delete(f"/api/llm/folders/{cid}")
        assert resp.status_code == 403

    # ── new message-category endpoints ──────────────────────────────────

    def test_assign_via_message_endpoint(self, client):
        _ensure_llm_tables()
        from ai_mini_box.core.container import RepoContainer
        from ai_mini_box.infrastructure.database import get_db as _get_db
        from ai_mini_box.core.models import Message

        folder = client.post("/api/llm/folders", json={"name": "MsgCat", "color": "#2563eb"}).json()

        with _get_db() as session:
            repos = RepoContainer(session)
            msg = repos.messages.add(Message(text="msg cat test", source="telegram"))
            mid = msg.id
            session.commit()

        resp = client.post(f"/api/messages/{mid}/categories", json={"category_id": folder["id"]})
        assert resp.status_code == 201
        assert resp.json()["ok"] is True

    def test_assign_message_endpoint_404_message(self, client):
        _ensure_llm_tables()
        folder = client.post("/api/llm/folders", json={"name": "MsgCat404M", "color": "#2563eb"}).json()
        resp = client.post("/api/messages/99999/categories", json={"category_id": folder["id"]})
        assert resp.status_code == 404

    def test_assign_message_endpoint_404_category(self, client):
        _ensure_llm_tables()
        from ai_mini_box.core.container import RepoContainer
        from ai_mini_box.infrastructure.database import get_db as _get_db
        from ai_mini_box.core.models import Message

        with _get_db() as session:
            repos = RepoContainer(session)
            msg = repos.messages.add(Message(text="cat 404", source="telegram"))
            mid = msg.id
            session.commit()

        resp = client.post(f"/api/messages/{mid}/categories", json={"category_id": 999})
        assert resp.status_code == 404

    def test_assign_message_endpoint_409(self, client):
        _ensure_llm_tables()
        from ai_mini_box.core.container import RepoContainer
        from ai_mini_box.infrastructure.database import get_db as _get_db
        from ai_mini_box.core.models import Message

        folder = client.post("/api/llm/folders", json={"name": "MsgCat409", "color": "#2563eb"}).json()

        with _get_db() as session:
            repos = RepoContainer(session)
            msg = repos.messages.add(Message(text="dup", source="telegram"))
            mid = msg.id
            session.commit()

        client.post(f"/api/messages/{mid}/categories", json={"category_id": folder["id"]})
        resp = client.post(f"/api/messages/{mid}/categories", json={"category_id": folder["id"]})
        assert resp.status_code == 409

    def test_unassign_via_message_endpoint(self, client):
        _ensure_llm_tables()
        from ai_mini_box.core.container import RepoContainer
        from ai_mini_box.infrastructure.database import get_db as _get_db
        from ai_mini_box.core.models import Message

        folder = client.post("/api/llm/folders", json={"name": "UnassignMsg", "color": "#2563eb"}).json()

        with _get_db() as session:
            repos = RepoContainer(session)
            msg = repos.messages.add(Message(text="unassign me", source="telegram"))
            mid = msg.id
            session.commit()

        client.post(f"/api/messages/{mid}/categories", json={"category_id": folder["id"]})
        resp = client.delete(f"/api/messages/{mid}/categories/{folder['id']}")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_unassign_not_found(self, client):
        _ensure_llm_tables()
        resp = client.delete("/api/messages/1/categories/999")
        assert resp.status_code == 404

    def test_unassign_system_blocked(self, client):
        _ensure_llm_tables()
        MC, MCA = None, None
        try:
            from ai_mini_box_llm.models import MessageCategory, MessageCategoryAssignment
            MC, MCA = MessageCategory, MessageCategoryAssignment
        except ImportError:
            pytest.skip("LLM plugin not installed")

        from ai_mini_box.infrastructure.database import get_db as _get_db
        from ai_mini_box.core.container import RepoContainer
        from ai_mini_box.core.models import Message

        with _get_db() as session:
            repos = RepoContainer(session)
            msg = repos.messages.add(Message(text="system block", source="telegram"))
            mid = msg.id

            cat = MC(name="SysCat", color="#2563eb", is_system=True)
            session.add(cat)
            session.flush()
            session.refresh(cat)

            assign = MCA(message_id=mid, category_id=cat.id, assigned_by="system")
            session.add(assign)
            session.commit()

            resp = client.delete(f"/api/messages/{mid}/categories/{cat.id}")
            assert resp.status_code == 403

    def test_batch_assign(self, client):
        _ensure_llm_tables()
        from ai_mini_box.core.container import RepoContainer
        from ai_mini_box.infrastructure.database import get_db as _get_db
        from ai_mini_box.core.models import Message

        folder = client.post("/api/llm/folders", json={"name": "Batch", "color": "#2563eb"}).json()
        mids = []

        with _get_db() as session:
            repos = RepoContainer(session)
            for i in range(3):
                msg = repos.messages.add(Message(text=f"batch {i}", source="telegram"))
                mids.append(msg.id)
            session.commit()

        resp = client.post("/api/llm/batch-assign", json={
            "message_ids": mids,
            "category_id": folder["id"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["assigned"] == 3
        assert data["errors"] == []

    def test_batch_assign_category_not_found(self, client):
        _ensure_llm_tables()
        resp = client.post("/api/llm/batch-assign", json={
            "message_ids": [1],
            "category_id": 999,
        })
        assert resp.status_code == 404

    def test_batch_assign_partial_errors(self, client):
        _ensure_llm_tables()
        folder = client.post("/api/llm/folders", json={"name": "BatchPartial", "color": "#2563eb"}).json()
        resp = client.post("/api/llm/batch-assign", json={
            "message_ids": [1, 99999, 2],
            "category_id": folder["id"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["assigned"] == 0
        assert len(data["errors"]) == 3

    def test_category_id_filter(self, client):
        _ensure_llm_tables()
        from ai_mini_box.core.container import RepoContainer
        from ai_mini_box.infrastructure.database import get_db as _get_db
        from ai_mini_box.core.models import Message

        folder = client.post("/api/llm/folders", json={"name": "FilterCat", "color": "#2563eb"}).json()

        with _get_db() as session:
            repos = RepoContainer(session)
            msg1 = repos.messages.add(Message(text="folder msg 1", source="telegram"))
            msg2 = repos.messages.add(Message(text="folder msg 2", source="telegram"))
            msg3 = repos.messages.add(Message(text="other msg", source="telegram"))
            session.commit()

        client.post(f"/api/llm/folders/{folder['id']}/assign", json={"message_id": msg1.id})
        client.post(f"/api/llm/folders/{folder['id']}/assign", json={"message_id": msg2.id})

        resp = client.get(f"/api/messages?category_id={folder['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        ids = {m["id"] for m in data}
        assert msg1.id in ids
        assert msg2.id in ids
        assert msg3.id not in ids

    def test_category_id_filter_empty(self, client):
        _ensure_llm_tables()
        resp = client.get("/api/messages?category_id=999")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_set_message_contact(self, client):
        _ensure_llm_tables()
        from ai_mini_box.infrastructure.database import get_db as _get_db, Base, get_engine
        from ai_mini_box.core.container import RepoContainer
        from ai_mini_box.core.models import Message, Contact
        import ai_mini_box.infrastructure.orm_models  # noqa: F401
        Base.metadata.create_all(get_engine())

        with _get_db() as session:
            repos = RepoContainer(session)
            msg = repos.messages.add(Message(text="link me", source="telegram"))
            mid = msg.id
            contact = repos.contacts.add(Contact(name="TestContact", source="manual"))
            cid = contact.id
            session.commit()

        resp = client.put(f"/api/messages/{mid}/contact", json={"contact_id": cid})
        assert resp.status_code == 200
        assert resp.json()["contact_id"] == cid

    def test_set_message_contact_msg_404(self, client):
        _ensure_llm_tables()
        resp = client.put("/api/messages/99999/contact", json={"contact_id": 1})
        assert resp.status_code == 404

    def test_set_message_contact_contact_404(self, client):
        _ensure_llm_tables()
        from ai_mini_box.infrastructure.database import get_db as _get_db
        from ai_mini_box.core.container import RepoContainer
        from ai_mini_box.core.models import Message

        with _get_db() as session:
            repos = RepoContainer(session)
            msg = repos.messages.add(Message(text="no contact", source="telegram"))
            mid = msg.id
            session.commit()

        resp = client.put(f"/api/messages/{mid}/contact", json={"contact_id": 999})
        assert resp.status_code == 404


class TestMessageOrders:
    def test_get_order_null(self, client):
        from ai_mini_box.infrastructure.database import get_db as _get_db, Base, get_engine
        from ai_mini_box.core.container import RepoContainer
        from ai_mini_box.core.models import Message
        import ai_mini_box.infrastructure.orm_models  # noqa: F401
        Base.metadata.create_all(get_engine())

        with _get_db() as session:
            repos = RepoContainer(session)
            msg = repos.messages.add(Message(text="no order", source="telegram"))
            mid = msg.id
            session.commit()

        resp = client.get(f"/api/messages/{mid}/order")
        assert resp.status_code == 200
        assert resp.json() is None

    def test_get_order_404(self, client):
        from ai_mini_box.infrastructure.database import Base, get_engine
        import ai_mini_box.infrastructure.orm_models  # noqa: F401
        Base.metadata.create_all(get_engine())
        resp = client.get("/api/messages/99999/order")
        assert resp.status_code == 404

    def test_create_order_success(self, client):
        from ai_mini_box.infrastructure.database import get_db as _get_db, Base, get_engine
        from ai_mini_box.core.container import RepoContainer
        from ai_mini_box.core.models import Message, Contact
        import ai_mini_box.infrastructure.orm_models  # noqa: F401
        Base.metadata.create_all(get_engine())

        with _get_db() as session:
            repos = RepoContainer(session)
            contact = repos.contacts.add(Contact(name="OrderContact", source="manual"))
            cid = contact.id
            msg = repos.messages.add(Message(text="create order pls", source="telegram", contact_id=cid))
            mid = msg.id
            session.commit()

        resp = client.post(f"/api/messages/{mid}/create-order", json={"total_kopecks": 150000, "notes": "Срочно"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_kopecks"] == 150000
        assert data["contact_id"] == cid
        assert data["source_message_id"] == mid
        assert data["status"] == "new"

    def test_create_order_duplicate(self, client):
        from ai_mini_box.infrastructure.database import get_db as _get_db
        from ai_mini_box.core.container import RepoContainer
        from ai_mini_box.core.models import Message, Contact, Order
        import ai_mini_box.infrastructure.orm_models  # noqa: F401
        from ai_mini_box.infrastructure.database import Base, get_engine
        Base.metadata.create_all(get_engine())

        with _get_db() as session:
            repos = RepoContainer(session)
            contact = repos.contacts.add(Contact(name="DupContact", source="manual"))
            cid = contact.id
            msg = repos.messages.add(Message(text="dup order", source="telegram", contact_id=cid))
            mid = msg.id
            order = repos.orders.add(Order(contact_id=cid, source_message_id=mid, total_kopecks=100))
            msg.extracted_order_id = order.id
            repos.messages.update(msg)
            session.commit()

        resp = client.post(f"/api/messages/{mid}/create-order", json={})
        assert resp.status_code == 409

    def test_create_order_no_contact(self, client):
        from ai_mini_box.infrastructure.database import get_db as _get_db, Base, get_engine
        from ai_mini_box.core.container import RepoContainer
        from ai_mini_box.core.models import Message
        import ai_mini_box.infrastructure.orm_models  # noqa: F401
        Base.metadata.create_all(get_engine())

        with _get_db() as session:
            repos = RepoContainer(session)
            msg = repos.messages.add(Message(text="no contact", source="telegram"))
            mid = msg.id
            session.commit()

        resp = client.post(f"/api/messages/{mid}/create-order", json={})
        assert resp.status_code == 400
        assert "contact" in resp.json()["detail"].lower()
