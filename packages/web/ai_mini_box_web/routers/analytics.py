from datetime import datetime, timedelta
from functools import wraps

from cachetools import TTLCache
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ai_mini_box.core.models import OrderStatus
from ai_mini_box.infrastructure.orm_models import (
    ContactModel,
    MessageModel,
    OrderModel,
    OrderItemModel,
)
from ai_mini_box_web.dependencies import _get_db_session

router = APIRouter()

_cache = TTLCache(maxsize=128, ttl=300)


def cached(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = (func.__name__, tuple(sorted((k, v) for k, v in kwargs.items() if k != "session")))
            if key in _cache:
                return _cache[key]
            result = func(*args, **kwargs)
            _cache[key] = result
            return result
        return wrapper
    return decorator


def _days_ago(days: int | None) -> datetime:
    if days is None or days <= 0:
        return datetime(2000, 1, 1)
    return datetime.now() - timedelta(days=days)


@router.get("/summary")
@cached()
def analytics_summary(
    days: int = Query(30, le=3650),
    session: Session = Depends(_get_db_session),
):
    since = _days_ago(days)
    return {
        "new_messages": session.execute(
            select(func.count(MessageModel.id)).where(MessageModel.received_at >= since)
        ).scalar() or 0,
        "new_contacts": session.execute(
            select(func.count(ContactModel.id)).where(ContactModel.created_at >= since)
        ).scalar() or 0,
        "new_orders": session.execute(
            select(func.count(OrderModel.id)).where(OrderModel.created_at >= since)
        ).scalar() or 0,
        "revenue_today": session.execute(
            select(func.coalesce(func.sum(OrderModel.total_kopecks), 0))
            .where(
                OrderModel.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                OrderModel.status == OrderStatus.COMPLETED,
            )
        ).scalar() or 0,
    }


@router.get("/messages")
@cached()
def analytics_messages(
    days: int = Query(30, le=3650),
    session: Session = Depends(_get_db_session),
):
    rows = session.execute(
        select(
            func.date(MessageModel.received_at).label("date"),
            func.count(MessageModel.id).label("count"),
        )
        .where(MessageModel.received_at >= _days_ago(days))
        .group_by(func.date(MessageModel.received_at))
        .order_by(func.date(MessageModel.received_at))
    ).all()
    return [{"date": str(r.date), "count": r.count} for r in rows]


@router.get("/orders")
@cached()
def analytics_orders(
    days: int = Query(30, le=3650),
    session: Session = Depends(_get_db_session),
):
    rows = session.execute(
        select(
            func.date(OrderModel.created_at).label("date"),
            func.count(OrderModel.id).label("count"),
        )
        .where(OrderModel.created_at >= _days_ago(days))
        .group_by(func.date(OrderModel.created_at))
        .order_by(func.date(OrderModel.created_at))
    ).all()
    return [{"date": str(r.date), "count": r.count} for r in rows]


@router.get("/revenue")
@cached()
def analytics_revenue(
    days: int = Query(30, le=3650),
    session: Session = Depends(_get_db_session),
):
    rows = session.execute(
        select(
            func.date(OrderModel.created_at).label("date"),
            func.coalesce(func.sum(OrderModel.total_kopecks), 0).label("total"),
        )
        .where(
            OrderModel.created_at >= _days_ago(days),
            OrderModel.status == OrderStatus.COMPLETED,
        )
        .group_by(func.date(OrderModel.created_at))
        .order_by(func.date(OrderModel.created_at))
    ).all()
    return [{"date": str(r.date), "total_kopecks": r.total} for r in rows]


@router.get("/channels")
@cached()
def analytics_channels(
    days: int = Query(30, le=3650),
    session: Session = Depends(_get_db_session),
):
    rows = session.execute(
        select(
            MessageModel.source,
            func.count(MessageModel.id).label("count"),
        )
        .where(MessageModel.received_at >= _days_ago(days))
        .group_by(MessageModel.source)
    ).all()
    return [{"source": r.source, "count": r.count} for r in rows]


@router.get("/top-contacts")
@cached()
def analytics_top_contacts(
    limit: int = Query(10, ge=1, le=50),
    days: int = Query(30, le=3650),
    session: Session = Depends(_get_db_session),
):
    rows = session.execute(
        select(
            ContactModel.id,
            ContactModel.name,
            ContactModel.total_spent,
            func.count(OrderModel.id).label("order_count"),
        )
        .outerjoin(OrderModel, OrderModel.contact_id == ContactModel.id)
        .where(ContactModel.total_spent > 0)
        .group_by(ContactModel.id, ContactModel.name, ContactModel.total_spent)
        .order_by(ContactModel.total_spent.desc())
        .limit(limit)
    ).all()
    return [{"id": r.id, "name": r.name, "total_spent": r.total_spent, "order_count": r.order_count} for r in rows]


@router.get("/funnel")
@cached()
def analytics_funnel(
    days: int = Query(30, le=3650),
    session: Session = Depends(_get_db_session),
):
    since = _days_ago(days)
    total_messages = session.execute(
        select(func.count(MessageModel.id)).where(MessageModel.received_at >= since)
    ).scalar() or 0
    linked_messages = session.execute(
        select(func.count(MessageModel.id))
        .where(MessageModel.received_at >= since, MessageModel.contact_id.isnot(None))
    ).scalar() or 0
    orders_total = session.execute(
        select(func.count(OrderModel.id)).where(OrderModel.created_at >= since)
    ).scalar() or 0
    orders_completed = session.execute(
        select(func.count(OrderModel.id))
        .where(OrderModel.created_at >= since, OrderModel.status == OrderStatus.COMPLETED)
    ).scalar() or 0
    return {
        "steps": [
            {"label": "Сообщения", "count": total_messages},
            {"label": "Привязаны к контакту", "count": linked_messages},
            {"label": "Заказы", "count": orders_total},
            {"label": "Выполнены", "count": orders_completed},
        ]
    }


def _moving_avg_forecast(values: list[float], days: int = 30):
    if len(values) < 7:
        return None
    window = min(7, len(values))
    avg = sum(values[-window:]) / window
    std = (sum((v - avg) ** 2 for v in values[-window:]) / window) ** 0.5
    last_date = datetime.now().date()
    predicted = []
    for i in range(1, days + 1):
        d = last_date + timedelta(days=i)
        predicted.append({
            "date": str(d),
            "predicted": round(avg, 2),
            "lower_bound": round(max(0, avg - 2 * std), 2),
            "upper_bound": round(avg + 2 * std, 2),
        })
    return predicted


def _forecast_with_sklearn(rows: list) -> list | None:
    try:
        from sklearn.linear_model import LinearRegression
        import numpy as np
    except ImportError:
        return None
    if len(rows) < 3:
        return None
    X = np.array(range(len(rows))).reshape(-1, 1)
    y = np.array([r.total for r in rows])
    model = LinearRegression()
    model.fit(X, y)
    last_date = datetime.now().date()
    n = len(rows)
    residuals = y - model.predict(X)
    std = residuals.std()
    predicted = []
    for i in range(1, 31):
        d = last_date + timedelta(days=i)
        val = float(model.predict(np.array([[n + i - 1]]))[0])
        predicted.append({
            "date": str(d),
            "predicted": round(max(0, val), 2),
            "lower_bound": round(max(0, val - 2 * std), 2),
            "upper_bound": round(val + 2 * std, 2),
        })
    return predicted


@router.get("/forecast")
@cached()
def analytics_forecast(
    days: int = Query(30, le=3650),
    session: Session = Depends(_get_db_session),
):
    since = _days_ago(days)
    rows = session.execute(
        select(
            func.date(OrderModel.created_at).label("date"),
            func.coalesce(func.sum(OrderModel.total_kopecks), 0).label("total"),
        )
        .where(
            OrderModel.created_at >= since,
            OrderModel.status == OrderStatus.COMPLETED,
        )
        .group_by(func.date(OrderModel.created_at))
        .order_by(func.date(OrderModel.created_at))
    ).all()

    values = [r.total for r in rows]
    sk_result = _forecast_with_sklearn(rows)
    if sk_result is not None:
        return {"predicted": sk_result, "method": "sklearn"}
    ma_result = _moving_avg_forecast(values)
    if ma_result is not None:
        return {"predicted": ma_result, "method": "moving_avg"}
    return {"predicted": None, "method": None}


@router.get("/retention")
@cached()
def analytics_retention(
    days: int = Query(90, ge=7, le=365),
    session: Session = Depends(_get_db_session),
):
    try:
        import pandas as pd
    except ImportError:
        return None

    since = _days_ago(days)
    msg_rows = session.execute(
        select(
            MessageModel.contact_id,
            func.date(MessageModel.received_at).label("date"),
        )
        .where(
            MessageModel.received_at >= since,
            MessageModel.contact_id.isnot(None),
        )
        .order_by(MessageModel.received_at)
    ).all()

    if not msg_rows:
        return None

    df = pd.DataFrame([(r.contact_id, r.date) for r in msg_rows], columns=["contact_id", "date"])
    df["date"] = pd.to_datetime(df["date"])
    df["week"] = df["date"].dt.isocalendar().year.astype(str) + "-W" + df["date"].dt.isocalendar().week.astype(str).str.zfill(2)

    cohort = df.groupby("contact_id")["week"].min().reset_index(name="cohort_week")
    merged = df.merge(cohort, on="contact_id")
    merged["period"] = merged.groupby("contact_id").cumcount()
    retention = merged.groupby(["cohort_week", "period"]).agg(users=("contact_id", "nunique")).reset_index()
    total = cohort.groupby("cohort_week").size().reset_index(name="total_users")
    retention = retention.merge(total, on="cohort_week")
    retention["pct"] = (retention["users"] / retention["total_users"] * 100).round(1)
    retention = retention.sort_values(["cohort_week", "period"])

    return [
        {"cohort_week": r["cohort_week"], "period": int(r["period"]), "pct": r["pct"]}
        for _, r in retention.iterrows()
    ]


@router.get("/ltv")
@cached()
def analytics_ltv(
    days: int = Query(365, le=3650),
    session: Session = Depends(_get_db_session),
):
    try:
        import pandas as pd
    except ImportError:
        return None

    since = _days_ago(days)
    rows = session.execute(
        select(
            OrderModel.contact_id,
            OrderModel.total_kopecks,
            OrderModel.created_at,
            OrderModel.status,
        )
        .where(
            OrderModel.created_at >= since,
            OrderModel.contact_id.isnot(None),
            OrderModel.status == OrderStatus.COMPLETED,
        )
        .order_by(OrderModel.created_at)
    ).all()

    if not rows:
        return None

    df = pd.DataFrame(
        [(r.contact_id, r.total_kopecks, r.created_at) for r in rows],
        columns=["contact_id", "total_kopecks", "created_at"],
    )
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["week"] = df["created_at"].dt.isocalendar().year.astype(str) + "-W" + df["created_at"].dt.isocalendar().week.astype(str).str.zfill(2)

    cohort = df.groupby("contact_id")["week"].min().reset_index(name="cohort_week")
    merged = df.merge(cohort, on="contact_id")
    merged["period"] = merged.groupby("contact_id").cumcount()
    ltv = merged.groupby(["cohort_week", "period"]).agg(revenue=("total_kopecks", "sum")).reset_index()
    total_customers = cohort.groupby("cohort_week").size().reset_index(name="customers")
    ltv = ltv.merge(total_customers, on="cohort_week")
    ltv["ltv_kopecks"] = (ltv["revenue"] / ltv["customers"]).round(0).astype(int)
    ltv = ltv.sort_values(["cohort_week", "period"])

    return [
        {"cohort_week": r["cohort_week"], "period": int(r["period"]), "ltv_kopecks": int(r["ltv_kopecks"])}
        for _, r in ltv.iterrows()
    ]
