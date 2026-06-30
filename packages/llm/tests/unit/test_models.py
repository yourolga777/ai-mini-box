from __future__ import annotations

from ai_mini_box_llm.models import (
    MessageCategory,
    MessageCategoryAssignment,
    Template,
    TemplateUsageLog,
    TrainingLog,
    classify_category_keyword,
)


class FakeCategory:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description


class TestClassifyCategoryKeyword:
    def test_exact_match(self):
        cats = [FakeCategory("Цены"), FakeCategory("Заказ")]
        result = classify_category_keyword("вопрос по ценам", cats)
        assert result.name == "Цены"

    def test_no_match_fallback_drugoe(self):
        cats = [FakeCategory("Цены"), FakeCategory("Другое")]
        result = classify_category_keyword("привет", cats)
        assert result.name == "Другое"

    def test_no_match_fallback_first(self):
        cats = [FakeCategory("Цены"), FakeCategory("Заказ")]
        result = classify_category_keyword("привет", cats)
        assert result.name == "Цены"

    def test_empty_categories(self):
        result = classify_category_keyword("hello", [])
        assert result is None

    def test_case_insensitive(self):
        cats = [FakeCategory("заказ")]
        result = classify_category_keyword("ЗАКАЗ", cats)
        assert result.name == "заказ"


class TestTrainingLogModel:
    def test_create(self):
        log = TrainingLog(message_text="test", category_predicted="ВОПРОС", category_corrected="ЗАКАЗ")
        assert log.message_text == "test"
        assert log.category_predicted == "ВОПРОС"
        assert log.category_corrected == "ЗАКАЗ"

    def test_defaults(self):
        log = TrainingLog(message_text="hello")
        assert log.operator_approved is None
        assert log.operator_edited is None
        assert log.created_at is not None


class TestTemplateModel:
    def test_create(self):
        t = Template(scope="business", category="question", name="Test", slug="test", text="Hello {{name}}")
        assert t.id is not None
        assert t.scope == "business"

    def test_variables_property(self):
        t = Template(scope="system", category="order", name="Test", slug="test", text="Order {{order_id}}")
        t.variables = ["order_id", "name"]
        assert t.variables == ["order_id", "name"]

    def test_empty_variables(self):
        t = Template(scope="system", category="order", name="T", slug="t", text="Text")
        assert t.variables == []

    def test_success_rate_zero(self):
        t = Template(scope="business", category="question", name="T", slug="t", text="Text")
        assert t.success_rate == 0.0

    def test_success_rate_calculation(self):
        t = Template(scope="business", category="question", name="T", slug="t", text="Text")
        t.usage_count = 10
        t.success_count = 8
        assert t.success_rate == 80.0

    def test_triggers_property(self):
        t = Template(scope="system", category="complaint", name="Legal", slug="legal", text="Text")
        t.triggers = ["расторг", "отказ"]
        assert t.triggers == ["расторг", "отказ"]

    def test_defaults_property(self):
        t = Template(scope="business", category="order", name="Test", slug="test", text="Text")
        t.defaults = {"name": "клиент"}
        assert t.defaults == {"name": "клиент"}


class TestTemplateUsageLogModel:
    def test_create(self):
        log = TemplateUsageLog(template_id="abc", category="question")
        assert log.template_id == "abc"
        assert log.was_used == 1
        assert log.operator_edited == 0
