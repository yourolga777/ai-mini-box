from __future__ import annotations

from ai_mini_box_llm.models import Template, TemplateUsageLog
from ai_mini_box_llm.templates.store import TemplateCreate, TemplateStore


class _MockSession:
    def __init__(self):
        self._store: dict[str, object] = {}
        self._ids: dict[str, list] = {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def get(self, model_cls, pk):
        for obj in self._store.values():
            if isinstance(obj, model_cls) and getattr(obj, "id", None) == pk:
                return obj
        return None

    def add(self, obj):
        if not getattr(obj, "id", None):
            import uuid
            obj.id = uuid.uuid4().hex
        self._store[obj.id] = obj

    def flush(self):
        pass

    def refresh(self, obj):
        pass

    def execute(self, stmt):
        class _Result:
            def scalars(self):
                return self

            def all(self):
                return []

            def first(self):
                return None

            def scalar_one_or_none(self):
                return None

        return _Result()

    def close(self):
        pass

    def expunge(self, obj):
        pass


class _MockDbFactory:
    def __init__(self):
        self.session = _MockSession()

    def __call__(self):
        return self.session


class TestTemplateModel:
    def test_create_template(self):
        t = Template(scope="business", category="question", name="Test", slug="test", text="Hello {{name}}")
        t.variables = ["name"]
        assert t.scope == "business"
        assert t.variables == ["name"]
        assert t.success_rate == 0.0

    def test_success_rate_calculation(self):
        t = Template(scope="business", category="question", name="Test", slug="test", text="Hello")
        t.usage_count = 10
        t.success_count = 7
        assert t.success_rate == 70.0

    def test_json_properties(self):
        t = Template(scope="system", category="complaint", name="Legal", slug="legal", text="Text")
        t.triggers = ["расторг", "отказ"]
        t.defaults = {"date": "сегодня"}
        assert t.triggers == ["расторг", "отказ"]
        assert t.defaults == {"date": "сегодня"}

    def test_template_usage_log(self):
        log = TemplateUsageLog(template_id="abc123", message_id="456")
        assert log.was_used == 1
        assert log.operator_edited == 0


class TestTemplateStore:
    def setup_method(self):
        self.db_factory = _MockDbFactory()
        self.store = TemplateStore(self.db_factory)

    def test_create(self):
        data = TemplateCreate(
            scope="business",
            category="question",
            name="Приветствие",
            text="Здравствуйте, {{name}}!",
            variables=["name"],
        )
        t = self.store.create(data)
        assert t.id is not None
        assert t.scope == "business"

    def test_get_nonexistent(self):
        t = self.store.get("nonexistent")
        assert t is None

    def test_delete_soft(self):
        data = TemplateCreate(scope="business", category="order", name="Test", text="Test")
        t = self.store.create(data)
        assert self.store.delete(t.id, hard=False)
        deleted = self.store.get(t.id)
        assert deleted is None or deleted.is_archived == 1

    def test_find_by_triggers_empty(self):
        t = self.store.find_by_triggers("")
        assert t is None

    def test_fallback_returns_template(self):
        from ai_mini_box_llm.templates.store import FALLBACK_TEXTS
        t = self.store._get_fallback()
        assert t.scope == "fallback"
        assert t.text in FALLBACK_TEXTS
