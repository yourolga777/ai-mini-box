from ai_mini_box.core.exceptions import NotFoundError
from ai_mini_box.core.models import Contact, MessageSource
from ai_mini_box.infrastructure.repositories.contact_repo import SqliteContactRepo


def test_add_contact(db_session):
    repo = SqliteContactRepo(db_session)
    contact = Contact(name="Иван Петров", phone="+79991234567", email="ivan@mail.ru")
    added = repo.add(contact)
    assert added.id is not None
    assert added.name == "Иван Петров"


def test_get_by_id(db_session):
    repo = SqliteContactRepo(db_session)
    contact = repo.add(Contact(name="Test"))
    found = repo.get_by_id(contact.id)
    assert found is not None
    assert found.name == "Test"


def test_get_by_id_not_found(db_session):
    repo = SqliteContactRepo(db_session)
    assert repo.get_by_id(999) is None


def test_update(db_session):
    repo = SqliteContactRepo(db_session)
    contact = repo.add(Contact(name="Old"))
    contact.name = "New"
    updated = repo.update(contact)
    assert updated.name == "New"


def test_update_not_found(db_session):
    repo = SqliteContactRepo(db_session)
    contact = Contact(id=999, name="Ghost")
    try:
        repo.update(contact)
        assert False, "Expected NotFoundError"
    except NotFoundError:
        pass


def test_delete(db_session):
    repo = SqliteContactRepo(db_session)
    contact = repo.add(Contact(name="ToDelete"))
    assert repo.delete(contact.id) is True
    assert repo.get_by_id(contact.id) is None


def test_delete_not_found(db_session):
    repo = SqliteContactRepo(db_session)
    assert repo.delete(999) is False


def test_list(db_session):
    repo = SqliteContactRepo(db_session)
    repo.add(Contact(name="A"))
    repo.add(Contact(name="B"))
    repo.add(Contact(name="C"))
    items = repo.list()
    assert len(items) >= 3


def test_list_with_filters(db_session):
    repo = SqliteContactRepo(db_session)
    repo.add(Contact(name="Alice", source=MessageSource.MANUAL))
    repo.add(Contact(name="Bob", source=MessageSource.TELEGRAM))
    filtered = repo.list(source=MessageSource.TELEGRAM)
    assert len(filtered) == 1
    assert filtered[0].name == "Bob"


def test_search(db_session):
    repo = SqliteContactRepo(db_session)
    repo.add(Contact(name="Иван Петров", phone="+79991234567"))
    repo.add(Contact(name="Анна Смирнова", phone="+79997654321"))
    results = repo.search("иван")
    assert len(results) == 1
    assert results[0].name == "Иван Петров"


def test_list_pagination(db_session):
    repo = SqliteContactRepo(db_session)
    for i in range(10):
        repo.add(Contact(name=f"Contact {i}"))
    page1 = repo.list(limit=3, offset=0)
    page2 = repo.list(limit=3, offset=3)
    assert len(page1) == 3
    assert len(page2) == 3
    assert page1[0].name != page2[0].name
