from ai_mini_box.core.exceptions import NotFoundError
from ai_mini_box.core.models import Order, OrderStatus
from ai_mini_box.infrastructure.repositories.order_repo import SqliteOrderRepo


def test_add(db_session):
    repo = SqliteOrderRepo(db_session)
    order = repo.add(Order(contact_id=1, total_kopecks=450000))
    assert order.id is not None
    assert order.status == OrderStatus.NEW


def test_get_by_id(db_session):
    repo = SqliteOrderRepo(db_session)
    order = repo.add(Order(contact_id=1))
    assert repo.get_by_id(order.id).contact_id == 1


def test_get_by_id_not_found(db_session):
    repo = SqliteOrderRepo(db_session)
    assert repo.get_by_id(999) is None


def test_update_status(db_session):
    repo = SqliteOrderRepo(db_session)
    order = repo.add(Order(contact_id=1))
    order.status = OrderStatus.COMPLETED
    updated = repo.update(order)
    assert updated.status == OrderStatus.COMPLETED


def test_update_not_found(db_session):
    repo = SqliteOrderRepo(db_session)
    try:
        repo.update(Order(id=999))
        assert False
    except NotFoundError:
        pass


def test_list(db_session):
    repo = SqliteOrderRepo(db_session)
    repo.add(Order(contact_id=1))
    repo.add(Order(contact_id=2))
    items = repo.list()
    assert len(items) >= 2


def test_list_with_filters(db_session):
    repo = SqliteOrderRepo(db_session)
    repo.add(Order(contact_id=1, status=OrderStatus.NEW))
    repo.add(Order(contact_id=2, status=OrderStatus.COMPLETED))
    filtered = repo.list(status=OrderStatus.COMPLETED)
    assert len(filtered) == 1
    assert filtered[0].contact_id == 2


def test_list_pagination(db_session):
    repo = SqliteOrderRepo(db_session)
    for i in range(5):
        repo.add(Order(contact_id=i))
    page = repo.list(limit=2, offset=0)
    assert len(page) == 2
