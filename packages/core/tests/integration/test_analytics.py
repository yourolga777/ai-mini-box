from datetime import datetime, timedelta

import pytest
from sqlalchemy import text

from ai_mini_box.core.services.analytics import AnalyticsService


def _insert_data(session):
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    last_week = now - timedelta(days=7)

    session.execute(
        text("INSERT INTO contacts (id, name, source, total_spent) VALUES (:id, :name, :source, :total_spent)"),
        [{"id": 1, "name": "Alice", "source": "telegram", "total_spent": 0},
         {"id": 2, "name": "Bob", "source": "email", "total_spent": 0},
         {"id": 3, "name": "Charlie", "source": "telegram", "total_spent": 0},
         {"id": 4, "name": "Diana", "source": "whatsapp", "total_spent": 0}]
    )
    session.execute(
        text("INSERT INTO messages (id, source, contact_id, text, sent_response, received_at) VALUES (:id, :source, :contact_id, :text, :sent_response, :received_at)"),
        [{"id": 1, "source": "telegram", "contact_id": 1, "text": "Hello", "sent_response": False, "received_at": yesterday},
         {"id": 2, "source": "telegram", "contact_id": 1, "text": "Price?", "sent_response": False, "received_at": now},
         {"id": 3, "source": "email", "contact_id": 2, "text": "Order", "sent_response": False, "received_at": yesterday},
         {"id": 4, "source": "telegram", "contact_id": None, "text": "Spam", "sent_response": False, "received_at": now},
         {"id": 5, "source": "whatsapp", "contact_id": 4, "text": "Hi", "sent_response": False, "received_at": last_week}]
    )
    session.execute(
        text("INSERT INTO orders (id, contact_id, status, total_kopecks, created_at) VALUES (:id, :contact_id, :status, :total_kopecks, :created_at)"),
        [{"id": 1, "contact_id": 1, "status": "completed", "total_kopecks": 5000, "created_at": yesterday},
         {"id": 2, "contact_id": 1, "status": "completed", "total_kopecks": 3000, "created_at": now},
         {"id": 3, "contact_id": 2, "status": "new", "total_kopecks": 2000, "created_at": yesterday},
         {"id": 4, "contact_id": 4, "status": "cancelled", "total_kopecks": 1000, "created_at": last_week}]
    )
    session.commit()


class TestAnalyticsService:
    def test_summary_empty(self, db_session):
        s = AnalyticsService(db_session).summary()
        assert s.total_messages == 0
        assert s.total_contacts == 0
        assert s.total_orders == 0
        assert s.total_revenue_kopecks == 0
        assert s.new_messages_today == 0
        assert s.new_contacts_today == 0
        assert s.new_orders_today == 0
        assert s.active_conversations == 0
        assert s.conversion_rate == 0.0

    def test_summary_with_data(self, db_session):
        _insert_data(db_session)
        s = AnalyticsService(db_session).summary()
        assert s.total_messages == 5
        assert s.total_contacts == 4
        assert s.total_orders == 4
        assert s.total_revenue_kopecks == 10000
        assert s.new_messages_today >= 2
        assert s.new_contacts_today >= 4
        assert s.new_orders_today >= 1
        assert s.active_conversations >= 2

    def test_messages_over_time(self, db_session):
        _insert_data(db_session)
        pts = AnalyticsService(db_session).messages_over_time(30)
        assert len(pts) > 0
        assert all(p.count > 0 for p in pts)

    def test_orders_over_time(self, db_session):
        _insert_data(db_session)
        pts = AnalyticsService(db_session).orders_over_time(30)
        assert len(pts) > 0
        assert all(p.count > 0 for p in pts)

    def test_revenue_over_time_excludes_cancelled(self, db_session):
        _insert_data(db_session)
        pts = AnalyticsService(db_session).revenue_over_time(30)
        total = sum(p.revenue_kopecks for p in pts)
        assert total == 10000

    def test_channel_distribution(self, db_session):
        _insert_data(db_session)
        items = AnalyticsService(db_session).channel_distribution()
        channels = {i.channel: i.count for i in items}
        assert channels.get("telegram") == 3
        assert channels.get("email") == 1
        assert channels.get("whatsapp") == 1
        total_pct = sum(i.percentage for i in items)
        assert abs(total_pct - 100.0) < 0.1

    def test_channel_distribution_empty(self, db_session):
        items = AnalyticsService(db_session).channel_distribution()
        assert items == []

    def test_top_contacts(self, db_session):
        _insert_data(db_session)
        items = AnalyticsService(db_session).top_contacts(limit=3)
        assert len(items) > 0
        assert items[0].contact_id == 1
        assert items[0].total_spent_kopecks == 8000

    def test_conversion_funnel(self, db_session):
        _insert_data(db_session)
        f = AnalyticsService(db_session).conversion_funnel()
        assert f.total_messages == 5
        assert f.messages_with_contact == 4
        assert f.orders_created == 4
        assert f.orders_completed == 2
        assert f.conversion_to_order > 0
        assert f.conversion_to_completed > 0

    def test_ltv(self, db_session):
        _insert_data(db_session)
        l = AnalyticsService(db_session).ltv()
        assert l.total_customers == 1
        assert l.average_ltv_kopecks == 8000
        assert l.max_ltv_kopecks == 8000
        assert l.min_ltv_kopecks == 8000

    def test_ltv_empty(self, db_session):
        l = AnalyticsService(db_session).ltv()
        assert l.total_customers == 0
        assert l.average_ltv_kopecks == 0
        assert l.cohorts == []

    def test_retention(self, db_session):
        _insert_data(db_session)
        rows = AnalyticsService(db_session).retention(90)
        assert len(rows) > 0

    def test_forecast_returns_empty_without_sklearn(self, db_session):
        _insert_data(db_session)
        pts = AnalyticsService(db_session).forecast_orders(10)
        assert pts == []

    def test_forecast_with_mocked_sklearn(self, db_session):
        import types
        import numpy as np

        class MockLinearRegression:
            def fit(self, X, y):
                self.coef_ = [[0.5]]
                self.intercept_ = 1.0
            def predict(self, X):
                return np.array([1.0] * len(X))

        sklearn_mod = types.ModuleType("sklearn")
        linear_mod = types.ModuleType("sklearn.linear_model")
        linear_mod.LinearRegression = MockLinearRegression
        sklearn_mod.linear_model = linear_mod

        import sys
        old = {}
        for key in ("sklearn", "sklearn.linear_model"):
            old[key] = sys.modules.get(key)
        sys.modules["sklearn"] = sklearn_mod
        sys.modules["sklearn.linear_model"] = linear_mod

        try:
            _insert_data(db_session)
            pts = AnalyticsService(db_session).forecast_orders(5)
            assert len(pts) == 5
            assert pts[0].date > "2026"
        finally:
            for key, val in old.items():
                if val is not None:
                    sys.modules[key] = val
                else:
                    sys.modules.pop(key, None)

    def test_cli_summary_runs(self, db_session, capsys, monkeypatch):
        _insert_data(db_session)

        from ai_mini_box.tools.analytics import _run
        from ai_mini_box.core.services.analytics import AnalyticsService

        service = AnalyticsService(db_session)
        _run(service, "summary", 30, "text")
        out = capsys.readouterr().out
        assert "total_messages" in out or "Messages" in out

    def test_cli_json_output(self, db_session, capsys, monkeypatch):
        _insert_data(db_session)

        from ai_mini_box.tools.analytics import _run
        from ai_mini_box.core.services.analytics import AnalyticsService
        import json

        service = AnalyticsService(db_session)
        _run(service, "summary", 30, "json")
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["total_messages"] == 5
