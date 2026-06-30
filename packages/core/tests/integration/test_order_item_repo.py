from ai_mini_box.core.exceptions import NotFoundError
from ai_mini_box.core.models import Order, OrderItem, OrderStatus
from ai_mini_box.infrastructure.orm_models import OrderModel
from ai_mini_box.infrastructure.repositories.order_repo import SqliteOrderItemRepo, SqliteOrderRepo


def _create_order(db_session) -> int:
    repo = SqliteOrderRepo(db_session)
    return repo.add(Order(contact_id=1)).id


def test_add(db_session):
    order_id = _create_order(db_session)
    repo = SqliteOrderItemRepo(db_session)
    item = repo.add(OrderItem(order_id=order_id, product_name="Widget", quantity=2, price_kopecks=1000))
    assert item.id is not None
    assert item.product_name == "Widget"


def test_list_by_order(db_session):
    order_id = _create_order(db_session)
    repo = SqliteOrderItemRepo(db_session)
    repo.add(OrderItem(order_id=order_id, product_name="A", quantity=1, price_kopecks=500))
    repo.add(OrderItem(order_id=order_id, product_name="B", quantity=3, price_kopecks=200))
    items = repo.list_by_order(order_id)
    assert len(items) == 2


def test_list_by_order_empty(db_session):
    order_id = _create_order(db_session)
    repo = SqliteOrderItemRepo(db_session)
    items = repo.list_by_order(order_id)
    assert items == []


def test_get_by_id(db_session):
    order_id = _create_order(db_session)
    repo = SqliteOrderItemRepo(db_session)
    created = repo.add(OrderItem(order_id=order_id, product_name="X", quantity=1, price_kopecks=500))
    found = repo.get_by_id(created.id)
    assert found is not None
    assert found.product_name == "X"


def test_get_by_id_not_found(db_session):
    repo = SqliteOrderItemRepo(db_session)
    assert repo.get_by_id(999) is None


def test_update(db_session):
    order_id = _create_order(db_session)
    repo = SqliteOrderItemRepo(db_session)
    item = repo.add(OrderItem(order_id=order_id, product_name="X", quantity=1, price_kopecks=500))
    item.quantity = 5
    updated = repo.update(item)
    assert updated.quantity == 5


def test_update_not_found(db_session):
    repo = SqliteOrderItemRepo(db_session)
    try:
        repo.update(OrderItem(id=999, order_id=1, product_name="X"))
        assert False
    except NotFoundError:
        pass


def test_delete(db_session):
    order_id = _create_order(db_session)
    repo = SqliteOrderItemRepo(db_session)
    item = repo.add(OrderItem(order_id=order_id, product_name="X", quantity=1, price_kopecks=500))
    repo.delete(item.id)
    assert repo.get_by_id(item.id) is None


def test_delete_not_found(db_session):
    repo = SqliteOrderItemRepo(db_session)
    try:
        repo.delete(999)
        assert False
    except NotFoundError:
        pass


def test_recalc_total_on_add(db_session):
    order_id = _create_order(db_session)
    order_repo = SqliteOrderRepo(db_session)
    item_repo = SqliteOrderItemRepo(db_session)
    item_repo.add(OrderItem(order_id=order_id, product_name="A", quantity=2, price_kopecks=1000))
    item_repo.add(OrderItem(order_id=order_id, product_name="B", quantity=3, price_kopecks=500))
    order = order_repo.get_by_id(order_id)
    assert order.total_kopecks == 2 * 1000 + 3 * 500  # 3500


def test_recalc_total_on_delete(db_session):
    order_id = _create_order(db_session)
    order_repo = SqliteOrderRepo(db_session)
    item_repo = SqliteOrderItemRepo(db_session)
    item1 = item_repo.add(OrderItem(order_id=order_id, product_name="A", quantity=2, price_kopecks=1000))
    item_repo.add(OrderItem(order_id=order_id, product_name="B", quantity=3, price_kopecks=500))
    item_repo.delete(item1.id)
    order = order_repo.get_by_id(order_id)
    assert order.total_kopecks == 3 * 500  # 1500


def test_recalc_total_on_update(db_session):
    order_id = _create_order(db_session)
    order_repo = SqliteOrderRepo(db_session)
    item_repo = SqliteOrderItemRepo(db_session)
    item = item_repo.add(OrderItem(order_id=order_id, product_name="A", quantity=2, price_kopecks=1000))
    item.quantity = 5
    item_repo.update(item)
    order = order_repo.get_by_id(order_id)
    assert order.total_kopecks == 5 * 1000  # 5000


def test_cascade_delete(db_session):
    order_id = _create_order(db_session)
    item_repo = SqliteOrderItemRepo(db_session)
    item_repo.add(OrderItem(order_id=order_id, product_name="A", quantity=1, price_kopecks=100))
    orm_obj = db_session.get(OrderModel, order_id)
    db_session.delete(orm_obj)
    db_session.flush()
    items = item_repo.list_by_order(order_id)
    assert items == []
