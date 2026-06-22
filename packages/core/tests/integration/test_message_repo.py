from ai_mini_box.core.models import Message, MessageSource, Topic
from ai_mini_box.infrastructure.repositories.message_repo import SqliteMessageRepo


def test_add(db_session):
    repo = SqliteMessageRepo(db_session)
    msg = repo.add(Message(text="Hello", source=MessageSource.TELEGRAM))
    assert msg.id is not None
    assert msg.text == "Hello"


def test_get_by_id(db_session):
    repo = SqliteMessageRepo(db_session)
    msg = repo.add(Message(text="Test"))
    assert repo.get_by_id(msg.id).text == "Test"


def test_get_by_id_not_found(db_session):
    repo = SqliteMessageRepo(db_session)
    assert repo.get_by_id(999) is None


def test_list(db_session):
    repo = SqliteMessageRepo(db_session)
    repo.add(Message(text="A"))
    repo.add(Message(text="B"))
    items = repo.list()
    assert len(items) >= 2


def test_list_with_filters(db_session):
    repo = SqliteMessageRepo(db_session)
    repo.add(Message(text="1", source=MessageSource.TELEGRAM))
    repo.add(Message(text="2", source=MessageSource.EMAIL))
    filtered = repo.list(source=MessageSource.EMAIL)
    assert len(filtered) == 1
    assert filtered[0].text == "2"


def test_search(db_session):
    repo = SqliteMessageRepo(db_session)
    repo.add(Message(text="Сколько стоит доставка?", topic=Topic.PRICES))
    repo.add(Message(text="Хочу заказать", topic=Topic.ORDER))
    results = repo.search("доставка")
    assert len(results) == 1


def test_search_with_topic(db_session):
    repo = SqliteMessageRepo(db_session)
    repo.add(Message(text="Цена на товар", topic=Topic.PRICES))
    repo.add(Message(text="Цена на услугу", topic=Topic.PRICES))
    repo.add(Message(text="График работы", topic=Topic.SCHEDULE))
    results = repo.search("цена", topic="Цены")
    assert len(results) == 2
