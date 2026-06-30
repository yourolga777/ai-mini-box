from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ai_mini_box.infrastructure.database import Base
import ai_mini_box.infrastructure.orm_models  # noqa: F401 — registers messages table on Base.metadata
from ai_mini_box_llm.models import MessageCategory, MessageCategoryAssignment


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


class TestMessageCategoryModel:
    def test_create_category(self, session):
        cat = MessageCategory(name="Тестовая", description="Описание", color="#ff0000")
        session.add(cat)
        session.flush()
        assert cat.id is not None
        assert cat.name == "Тестовая"
        assert cat.is_system is False

    def test_unique_name_constraint(self, session):
        cat1 = MessageCategory(name="Уникальная")
        session.add(cat1)
        session.flush()
        cat2 = MessageCategory(name="Уникальная")
        session.add(cat2)
        with pytest.raises(Exception):
            session.flush()

    def test_system_category(self, session):
        cat = MessageCategory(name="Системная", is_system=True)
        session.add(cat)
        session.flush()
        assert cat.is_system is True

    def test_default_color(self, session):
        cat = MessageCategory(name="Без цвета")
        session.add(cat)
        session.flush()
        assert cat.color == "#6b7280"

    def test_default_description(self, session):
        cat = MessageCategory(name="Без описания")
        session.add(cat)
        session.flush()
        assert cat.description == ""

    def test_default_assigned_by(self, session):
        cat = MessageCategory(name="Категория")
        session.add(cat)
        session.flush()
        assign = MessageCategoryAssignment(message_id=1, category_id=cat.id)
        session.add(assign)
        session.flush()
        assert assign.assigned_by == "manual"

    def test_manual_assignment(self, session):
        cat = MessageCategory(name="Категория")
        session.add(cat)
        session.flush()
        assign = MessageCategoryAssignment(message_id=1, category_id=cat.id, assigned_by="manual")
        session.add(assign)
        session.flush()
        assert assign.assigned_by == "manual"

    def test_category_assignment_relationship(self, session):
        cat = MessageCategory(name="Категория")
        session.add(cat)
        session.flush()

        assign1 = MessageCategoryAssignment(message_id=10, category_id=cat.id)
        assign2 = MessageCategoryAssignment(message_id=20, category_id=cat.id)
        session.add_all([assign1, assign2])
        session.flush()

        assert len(cat.assignments) == 2
        assert {a.message_id for a in cat.assignments} == {10, 20}

    def test_cascade_delete(self, session):
        cat = MessageCategory(name="Удаляемая")
        session.add(cat)
        session.flush()

        session.add(MessageCategoryAssignment(message_id=1, category_id=cat.id))
        session.flush()

        session.delete(cat)
        session.flush()

        remaining = session.query(MessageCategoryAssignment).filter_by(category_id=cat.id).all()
        assert len(remaining) == 0

    def test_multiple_categories(self, session):
        names = ["Цены", "Заказ", "Жалоба", "График", "Другое"]
        for n in names:
            session.add(MessageCategory(name=n, is_system=True))
        session.flush()

        cats = session.query(MessageCategory).all()
        assert len(cats) == 5

    def test_category_order(self, session):
        session.add(MessageCategory(name="B", is_system=True))
        session.add(MessageCategory(name="A", is_system=True))
        session.flush()

        cats = session.query(MessageCategory).order_by(MessageCategory.name).all()
        assert [c.name for c in cats] == ["A", "B"]
