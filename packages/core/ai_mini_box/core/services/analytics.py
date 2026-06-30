from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass
class AnalyticsSummary:
    total_messages: int
    total_contacts: int
    total_orders: int
    total_revenue_kopecks: int
    new_messages_today: int
    new_contacts_today: int
    new_orders_today: int
    active_conversations: int
    conversion_rate: float


@dataclass
class DateCount:
    date: str
    count: int


@dataclass
class RevenuePoint:
    date: str
    revenue_kopecks: int


@dataclass
class ChannelCount:
    channel: str
    count: int
    percentage: float


@dataclass
class ContactStats:
    contact_id: int
    contact_name: str
    total_orders: int
    total_spent_kopecks: int
    last_order_date: Optional[str]


@dataclass
class ConversionFunnel:
    total_messages: int
    messages_with_contact: int
    orders_created: int
    orders_completed: int
    conversion_to_order: float
    conversion_to_completed: float


@dataclass
class LtvStats:
    average_ltv_kopecks: int
    median_ltv_kopecks: int
    max_ltv_kopecks: int
    min_ltv_kopecks: int
    total_customers: int
    cohorts: list[CohortLtv]


@dataclass
class CohortLtv:
    cohort: str
    customer_count: int
    average_ltv_kopecks: int


@dataclass
class CohortRow:
    cohort: str
    periods: list[int]


@dataclass
class ForecastPoint:
    date: str
    predicted: int
    lower_bound: int
    upper_bound: int


class AnalyticsService:
    def __init__(self, session: Session):
        self.session = session

    def summary(self) -> AnalyticsSummary:
        total_messages = self._scalar("SELECT COUNT(*) FROM messages")
        total_contacts = self._scalar("SELECT COUNT(*) FROM contacts")
        total_orders = self._scalar("SELECT COUNT(*) FROM orders")
        total_revenue = self._scalar(
            "SELECT COALESCE(SUM(total_kopecks), 0) FROM orders WHERE status != 'cancelled'"
        )
        today = "date('now')"
        new_messages = self._scalar(
            f"SELECT COUNT(*) FROM messages WHERE date(received_at) = {today}"
        )
        new_contacts = self._scalar(
            f"SELECT COUNT(*) FROM contacts WHERE date(created_at) = {today}"
        )
        new_orders = self._scalar(
            f"SELECT COUNT(*) FROM orders WHERE date(created_at) = {today}"
        )
        active = self._scalar(
            "SELECT COUNT(DISTINCT contact_id) FROM messages WHERE contact_id IS NOT NULL AND received_at >= date('now', '-7 days')"
        )
        contacts_with_msgs = self._scalar(
            "SELECT COUNT(DISTINCT contact_id) FROM messages WHERE contact_id IS NOT NULL"
        )
        conversion_rate = 0.0
        if contacts_with_msgs > 0:
            conversion_rate = round(total_orders / contacts_with_msgs * 100, 1)
        return AnalyticsSummary(
            total_messages=total_messages,
            total_contacts=total_contacts,
            total_orders=total_orders,
            total_revenue_kopecks=total_revenue,
            new_messages_today=new_messages,
            new_contacts_today=new_contacts,
            new_orders_today=new_orders,
            active_conversations=active,
            conversion_rate=conversion_rate,
        )

    def messages_over_time(self, days: int = 30) -> list[DateCount]:
        rows = self._fetch(
            """SELECT date(received_at) AS date, COUNT(*) AS count
               FROM messages
               WHERE received_at >= datetime('now', :days || ' days')
               GROUP BY date(received_at) ORDER BY date""",
            {"days": f"-{days}"},
        )
        return [DateCount(date=r[0], count=r[1]) for r in rows]

    def orders_over_time(self, days: int = 30) -> list[DateCount]:
        rows = self._fetch(
            """SELECT date(created_at) AS date, COUNT(*) AS count
               FROM orders
               WHERE created_at >= datetime('now', :days || ' days')
               GROUP BY date(created_at) ORDER BY date""",
            {"days": f"-{days}"},
        )
        return [DateCount(date=r[0], count=r[1]) for r in rows]

    def revenue_over_time(self, days: int = 30) -> list[RevenuePoint]:
        rows = self._fetch(
            """SELECT date(created_at) AS date, COALESCE(SUM(total_kopecks), 0) AS revenue
               FROM orders
               WHERE created_at >= datetime('now', :days || ' days') AND status != 'cancelled'
               GROUP BY date(created_at) ORDER BY date""",
            {"days": f"-{days}"},
        )
        return [RevenuePoint(date=r[0], revenue_kopecks=r[1]) for r in rows]

    def channel_distribution(self) -> list[ChannelCount]:
        total = self._scalar("SELECT COUNT(*) FROM messages")
        if total == 0:
            return []
        rows = self._fetch(
            "SELECT source, COUNT(*) AS count FROM messages GROUP BY source ORDER BY count DESC"
        )
        return [
            ChannelCount(channel=r[0], count=r[1], percentage=round(r[1] / total * 100, 1))
            for r in rows
        ]

    def top_contacts(self, limit: int = 10) -> list[ContactStats]:
        rows = self._fetch(
            """SELECT c.id, c.name, COUNT(o.id) AS total_orders,
                      COALESCE(SUM(o.total_kopecks), 0) AS total_spent,
                      MAX(o.created_at) AS last_order_date
               FROM contacts c
               LEFT JOIN orders o ON o.contact_id = c.id
               GROUP BY c.id
               ORDER BY total_spent DESC
               LIMIT :limit""",
            {"limit": limit},
        )
        return [
            ContactStats(
                contact_id=r[0],
                contact_name=r[1],
                total_orders=r[2],
                total_spent_kopecks=r[3],
                last_order_date=str(r[4]) if r[4] else None,
            )
            for r in rows
        ]

    def _contact_funnel_count(self) -> int:
        return self._scalar(
            "SELECT COUNT(DISTINCT contact_id) FROM messages WHERE contact_id IS NOT NULL"
        )

    def conversion_funnel(self) -> ConversionFunnel:
        total_messages = self._scalar("SELECT COUNT(*) FROM messages")
        with_contact = self._scalar(
            "SELECT COUNT(*) FROM messages WHERE contact_id IS NOT NULL"
        )
        orders_created = self._scalar("SELECT COUNT(*) FROM orders")
        orders_completed = self._scalar(
            "SELECT COUNT(*) FROM orders WHERE status = 'completed'"
        )
        conv_to_order = 0.0
        conv_to_completed = 0.0
        if with_contact > 0:
            conv_to_order = round(orders_created / with_contact * 100, 1)
        if total_messages > 0:
            conv_to_completed = round(orders_completed / total_messages * 100, 1)
        return ConversionFunnel(
            total_messages=total_messages,
            messages_with_contact=with_contact,
            orders_created=orders_created,
            orders_completed=orders_completed,
            conversion_to_order=conv_to_order,
            conversion_to_completed=conv_to_completed,
        )

    def ltv(self) -> LtvStats:
        rows = self._fetch(
            """SELECT contact_id, SUM(total_kopecks) AS ltv
               FROM orders
               WHERE contact_id IS NOT NULL AND status = 'completed'
               GROUP BY contact_id"""
        )
        ltvs = [r[1] for r in rows]
        total = len(ltvs)
        if total == 0:
            return LtvStats(
                average_ltv_kopecks=0,
                median_ltv_kopecks=0,
                max_ltv_kopecks=0,
                min_ltv_kopecks=0,
                total_customers=0,
                cohorts=[],
            )
        average = round(sum(ltvs) / total)
        median = statistics.median_low(ltvs) if len(ltvs) > 1 else ltvs[0]
        return LtvStats(
            average_ltv_kopecks=average,
            median_ltv_kopecks=median,
            max_ltv_kopecks=max(ltvs),
            min_ltv_kopecks=min(ltvs),
            total_customers=total,
            cohorts=self._ltv_cohorts(rows),
        )

    def _ltv_cohorts(self, ltv_rows: list[tuple]) -> list[CohortLtv]:
        contact_ids = [r[0] for r in ltv_rows]
        if not contact_ids:
            return []
        placeholders = ",".join(f":cid_{i}" for i in range(len(contact_ids)))
        params = {f"cid_{i}": cid for i, cid in enumerate(contact_ids)}
        cohort_rows = self._fetch(
            f"""SELECT o.contact_id, strftime('%Y-%m', MIN(o.created_at)) AS cohort
                FROM orders o
                WHERE o.contact_id IN ({placeholders}) AND o.status = 'completed'
                GROUP BY o.contact_id""",
            params,
        )
        cohort_map: dict[str, list[int]] = {}
        ltv_map = {r[0]: r[1] for r in ltv_rows}
        for contact_id, cohort in cohort_rows:
            cohort_map.setdefault(cohort, []).append(ltv_map.get(contact_id, 0))
        result = []
        for cohort in sorted(cohort_map):
            vals = cohort_map[cohort]
            avg = round(sum(vals) / len(vals))
            result.append(
                CohortLtv(cohort=cohort, customer_count=len(vals), average_ltv_kopecks=avg)
            )
        return result

    def retention(self, days: int = 90) -> list[CohortRow]:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        first_orders = self._fetch(
            """SELECT contact_id, MIN(created_at) AS first_order
               FROM orders
               WHERE contact_id IS NOT NULL AND created_at >= :cutoff
               GROUP BY contact_id""",
            {"cutoff": cutoff},
        )
        if not first_orders:
            return []
        contact_first: dict[int, datetime] = {}
        contact_cohort: dict[int, str] = {}
        for contact_id, raw_first in first_orders:
            first_order = raw_first if isinstance(raw_first, datetime) else datetime.fromisoformat(str(raw_first).replace(" ", "T"))
            contact_first[contact_id] = first_order
            cohort_week = first_order.strftime("%Y-%U")
            contact_cohort[contact_id] = cohort_week

        cids = list(contact_cohort.keys())
        placeholders = ",".join(f":cid_{i}" for i in range(len(cids)))
        params: dict = {f"cid_{i}": cid for i, cid in enumerate(cids)}
        params["cutoff"] = cutoff
        all_orders = self._fetch(
            f"""SELECT contact_id, created_at
                FROM orders
                WHERE contact_id IN ({placeholders}) AND created_at >= :cutoff
                ORDER BY contact_id, created_at""",
            params,
        )
        cohort_weeks: dict[str, set[int]] = {c: set() for c in set(contact_cohort.values())}
        for contact_id, raw_order in all_orders:
            cohort = contact_cohort.get(contact_id)
            if not cohort:
                continue
            first_date = contact_first.get(contact_id)
            if not first_date:
                continue
            order_dt = raw_order if isinstance(raw_order, datetime) else datetime.fromisoformat(str(raw_order).replace(" ", "T"))
            week_num = self._week_diff(first_date, order_dt)
            cohort_weeks[cohort].add(week_num)

        result = []
        for cohort in sorted(cohort_weeks):
            members = [c for c, coh in contact_cohort.items() if coh == cohort]
            periods = []
            for w in range(1, 13):
                retained = sum(1 for c in members if w in cohort_weeks.get(cohort, set()))
                periods.append(retained)
            result.append(CohortRow(cohort=cohort, periods=periods))
        return result

    @staticmethod
    def _week_diff(start, order_date) -> int:
        if isinstance(start, str):
            start = datetime.fromisoformat(start)
        if isinstance(order_date, str):
            order_date = datetime.fromisoformat(order_date)
        diff = order_date - start
        return max(0, diff.days // 7)

    def forecast_orders(self, days: int = 30) -> list[ForecastPoint]:
        try:
            from sklearn.linear_model import LinearRegression
            import numpy as np
        except ImportError:
            return []

        rows = self._fetch(
            """SELECT date(created_at) AS date, COUNT(*) AS count
               FROM orders
               GROUP BY date(created_at) ORDER BY date"""
        )
        if len(rows) < 2:
            return []

        X = np.arange(len(rows)).reshape(-1, 1)
        y = np.array([r[1] for r in rows])
        model = LinearRegression()
        model.fit(X, y)
        future_X = np.arange(len(rows), len(rows) + days).reshape(-1, 1)
        preds = model.predict(future_X)
        residuals = y - model.predict(X)
        std = np.std(residuals) if len(residuals) > 1 else 0
        last_date = datetime.strptime(rows[-1][0], "%Y-%m-%d") if rows else datetime.now()
        result = []
        for i in range(days):
            d = (last_date + timedelta(days=i + 1)).strftime("%Y-%m-%d")
            p = max(0, int(round(preds[i])))
            lb = max(0, int(round(preds[i] - 1.96 * std))) if std > 0 else p
            ub = max(0, int(round(preds[i] + 1.96 * std))) if std > 0 else p
            result.append(ForecastPoint(date=d, predicted=p, lower_bound=lb, upper_bound=ub))
        return result

    def _scalar(self, sql: str, params: dict | None = None) -> int:
        result = self.session.execute(text(sql), params or {})
        return result.scalar() or 0

    def _fetch(self, sql: str, params: dict | list | None = None) -> list:
        if isinstance(params, list):
            result = self.session.execute(text(sql), params)
        else:
            result = self.session.execute(text(sql), params or {})
        return result.fetchall()
