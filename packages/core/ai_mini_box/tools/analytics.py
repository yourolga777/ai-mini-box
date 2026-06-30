from __future__ import annotations

import json
from datetime import date

import typer

from ai_mini_box.core.services.analytics import AnalyticsService
from ai_mini_box.infrastructure.database import get_db


def register(app: typer.Typer):
    @app.command()
    def analytics(
        command: str = typer.Argument("summary"),
        days: int = typer.Option(30, "--days", "-d", help="Days for time-series queries"),
        output: str = typer.Option("text", "--output", "--out", help="Output format: text or json"),
    ):
        """Business analytics and metrics."""
        if output not in ("text", "json"):
            typer.echo(f"Error: unsupported output format '{output}'. Use text or json.")
            raise typer.Exit(code=1)

        with get_db() as session:
            service = AnalyticsService(session)
            _run(service, command, days, output)


def _run(service: AnalyticsService, command: str, days: int, output: str):
    dispatch = {
        "summary": _cmd_summary,
        "funnel": _cmd_funnel,
        "ltv": _cmd_ltv,
        "retention": _cmd_retention,
        "forecast": _cmd_forecast,
        "messages": _cmd_messages,
        "orders": _cmd_orders,
        "revenue": _cmd_revenue,
        "channels": _cmd_channels,
        "contacts": _cmd_contacts,
    }
    fn = dispatch.get(command)
    if fn is None:
        typer.echo(f"Unknown command: {command}")
        typer.echo(f"Available: {', '.join(sorted(dispatch))}")
        raise typer.Exit(code=1)
    fn(service, days, output)


def _cmd_summary(service: AnalyticsService, days: int, output: str):
    s = service.summary()
    if output == "json":
        typer.echo(json.dumps(_asdict(s), ensure_ascii=False, indent=2, default=str))
        return
    _print_table([
        ("Messages", "total_messages"),
        ("Contacts", "total_contacts"),
        ("Orders", "total_orders"),
        ("Revenue (kopecks)", "total_revenue_kopecks"),
        ("New messages today", "new_messages_today"),
        ("New contacts today", "new_contacts_today"),
        ("New orders today", "new_orders_today"),
        ("Active conversations (7d)", "active_conversations"),
        ("Conversion rate (%)", "conversion_rate"),
    ], s)


def _cmd_funnel(service: AnalyticsService, days: int, output: str):
    f = service.conversion_funnel()
    if output == "json":
        typer.echo(json.dumps(_asdict(f), ensure_ascii=False, indent=2, default=str))
        return
    _print_table([
        ("Total messages", "total_messages"),
        ("Messages with contact", "messages_with_contact"),
        ("Orders created", "orders_created"),
        ("Orders completed", "orders_completed"),
        ("Conversion to order (%)", "conversion_to_order"),
        ("Conversion to completed (%)", "conversion_to_completed"),
    ], f)


def _cmd_ltv(service: AnalyticsService, days: int, output: str):
    l = service.ltv()
    if output == "json":
        typer.echo(json.dumps(_asdict(l), ensure_ascii=False, indent=2, default=str))
        return
    _print_table([
        ("Average LTV (kopecks)", "average_ltv_kopecks"),
        ("Median LTV (kopecks)", "median_ltv_kopecks"),
        ("Max LTV (kopecks)", "max_ltv_kopecks"),
        ("Min LTV (kopecks)", "min_ltv_kopecks"),
        ("Total customers", "total_customers"),
    ], l)
    if l.cohorts:
        typer.echo("\nCohorts:")
        for c in l.cohorts:
            typer.echo(f"  {c.cohort}: {c.customer_count} customers, avg {c.average_ltv_kopecks} kopecks")


def _cmd_retention(service: AnalyticsService, days: int, output: str):
    rows = service.retention(days)
    if output == "json":
        typer.echo(json.dumps([_asdict(r) for r in rows], ensure_ascii=False, indent=2, default=str))
        return
    if not rows:
        typer.echo("No retention data.")
        return
    header = "Cohort".ljust(12) + " " + " ".join(f"W{w:<4}" for w in range(1, 13))
    typer.echo(header)
    for r in rows:
        periods = " ".join(f"{p:<5}" for p in r.periods[:12])
        typer.echo(f"{r.cohort:<12} {periods}")


def _cmd_forecast(service: AnalyticsService, days: int, output: str):
    pts = service.forecast_orders(days)
    if output == "json":
        typer.echo(json.dumps([_asdict(p) for p in pts], ensure_ascii=False, indent=2, default=str))
        return
    if not pts:
        typer.echo("Forecast unavailable: insufficient data or sklearn not installed.")
        return
    typer.echo(f"{'Date':<14} {'Predicted':<12} {'Lower':<12} {'Upper':<12}")
    typer.echo("-" * 50)
    for p in pts:
        typer.echo(f"{p.date:<14} {p.predicted:<12} {p.lower_bound:<12} {p.upper_bound:<12}")


def _cmd_messages(service: AnalyticsService, days: int, output: str):
    pts = service.messages_over_time(days)
    _print_series(pts, "Messages per day", output)


def _cmd_orders(service: AnalyticsService, days: int, output: str):
    pts = service.orders_over_time(days)
    _print_series(pts, "Orders per day", output)


def _cmd_revenue(service: AnalyticsService, days: int, output: str):
    pts = service.revenue_over_time(days)
    if output == "json":
        typer.echo(json.dumps([_asdict(p) for p in pts], ensure_ascii=False, indent=2, default=str))
        return
    typer.echo(f"{'Date':<14} {'Revenue (kopecks)':<20}")
    typer.echo("-" * 34)
    for p in pts:
        typer.echo(f"{p.date:<14} {p.revenue_kopecks:<20}")


def _cmd_channels(service: AnalyticsService, days: int, output: str):
    items = service.channel_distribution()
    if output == "json":
        typer.echo(json.dumps([_asdict(i) for i in items], ensure_ascii=False, indent=2, default=str))
        return
    typer.echo(f"{'Channel':<20} {'Count':<10} {'%':<8}")
    typer.echo("-" * 38)
    for i in items:
        typer.echo(f"{i.channel:<20} {i.count:<10} {i.percentage:<8}")


def _cmd_contacts(service: AnalyticsService, days: int, output: str):
    items = service.top_contacts()
    if output == "json":
        typer.echo(json.dumps([_asdict(i) for i in items], ensure_ascii=False, indent=2, default=str))
        return
    typer.echo(f"{'ID':<6} {'Name':<20} {'Orders':<10} {'Spent (k)':<12} {'Last order':<14}")
    typer.echo("-" * 62)
    for i in items:
        last = i.last_order_date or "-"
        typer.echo(f"{i.contact_id:<6} {i.contact_name:<20} {i.total_orders:<10} {i.total_spent_kopecks:<12} {last:<14}")


def _print_series(pts: list, title: str, output: str):
    if output == "json":
        typer.echo(json.dumps([_asdict(p) for p in pts], ensure_ascii=False, indent=2, default=str))
        return
    typer.echo(f"{title} (last 30 days):")
    typer.echo(f"{'Date':<14} {'Count':<10}")
    typer.echo("-" * 24)
    for p in pts:
        typer.echo(f"{p.date:<14} {p.count:<10}")
    if not pts:
        typer.echo("No data.")


def _print_table(fields: list[tuple[str, str]], obj):
    for label, attr in fields:
        val = getattr(obj, attr, "")
        typer.echo(f"  {label:<35} {val}")


def _asdict(obj):
    if hasattr(obj, "__dataclass_fields__"):
        return {f.name: _asdict(getattr(obj, f.name)) for f in obj.__dataclass_fields__.values()}
    if isinstance(obj, list):
        return [_asdict(v) for v in obj]
    return obj
