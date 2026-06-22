from ai_mini_box.core.exceptions import NotFoundError
from ai_mini_box.core.models import Product
from ai_mini_box.infrastructure.repositories.product_repo import SqliteProductRepo


def test_add(db_session):
    repo = SqliteProductRepo(db_session)
    p = repo.add(Product(name="Футболка", price_kopecks=199900, stock=50))
    assert p.id is not None
    assert p.price_kopecks == 199900


def test_get_by_id(db_session):
    repo = SqliteProductRepo(db_session)
    p = repo.add(Product(name="Test"))
    assert repo.get_by_id(p.id).name == "Test"


def test_get_by_id_not_found(db_session):
    repo = SqliteProductRepo(db_session)
    assert repo.get_by_id(999) is None


def test_update(db_session):
    repo = SqliteProductRepo(db_session)
    p = repo.add(Product(name="Old", stock=10))
    p.stock = 20
    updated = repo.update(p)
    assert updated.stock == 20


def test_update_not_found(db_session):
    repo = SqliteProductRepo(db_session)
    try:
        repo.update(Product(id=999, name="Ghost"))
        assert False
    except NotFoundError:
        pass


def test_delete(db_session):
    repo = SqliteProductRepo(db_session)
    p = repo.add(Product(name="ToDelete"))
    assert repo.delete(p.id) is True
    assert repo.get_by_id(p.id) is None


def test_delete_not_found(db_session):
    repo = SqliteProductRepo(db_session)
    assert repo.delete(999) is False


def test_search(db_session):
    repo = SqliteProductRepo(db_session)
    repo.add(Product(name="Футболка белая", category="Одежда"))
    repo.add(Product(name="Кружка", category="Посуда"))
    results = repo.search("футболка")
    assert len(results) == 1


def test_list_with_filters(db_session):
    repo = SqliteProductRepo(db_session)
    repo.add(Product(name="A", stock=5))
    repo.add(Product(name="B", stock=0))
    filtered = repo.list(stock=0)
    assert len(filtered) == 1
    assert filtered[0].name == "B"


def test_list_pagination(db_session):
    repo = SqliteProductRepo(db_session)
    for i in range(5):
        repo.add(Product(name=f"P{i}"))
    page = repo.list(limit=2, offset=0)
    assert len(page) == 2
