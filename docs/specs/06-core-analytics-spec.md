# Спецификация: Сервис аналитики + CLI

> **Статус: ЗАКРЫТ** — Core-слой аналитики и CLI не реализованы.
> Аналитика работает через web-роутер (`routers/analytics.py`) напрямую, без core-сервиса.
> `core/services/analytics.py` и `tools/analytics.py` — пустые файлы.
> Если потребуется CLI-аналитика — переписать spec под текущую архитектуру.

**Разработчик:** Бэкенд-разработчик (core)

**Файлы:**
- `packages/core/ai_mini_box/core/services/analytics.py` — новый сервис
- `packages/core/ai_mini_box/infrastructure/repositories/analytics_repo.py` — SQL-запросы
- `packages/core/ai_mini_box/tools/analytics.py` — CLI-команды
- `packages/core/pyproject.toml` — опциональные зависимости

## 1. AnalyticsService

```python
class AnalyticsService:
    def __init__(self, session: Session):
        self.session = session

    def summary(self) -> AnalyticsSummary
    def messages_over_time(self, days: int = 30) -> list[DateCount]
    def orders_over_time(self, days: int = 30) -> list[DateCount]
    def revenue_over_time(self, days: int = 30) -> list[DateCount]
    def channel_distribution(self) -> list[ChannelCount]
    def top_contacts(self, limit: int = 10) -> list[ContactStats]
    def conversion_funnel(self) -> ConversionFunnel
    def ltv(self) -> LtvStats
    def retention(self, days: int = 90) -> list[CohortRow]
    def forecast_orders(self, days: int = 30) -> list[ForecastPoint]
```

Все методы — прямые SQL-запросы через `session.execute()`.

## 2. Модели данных

```python
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
```

## 3. Ключевые SQL-запросы

**summary:** 8 вложенных SELECT (total + today counts).

**messages_over_time / orders_over_time / revenue_over_time:**
```sql
SELECT date(created_at) AS date, COUNT(*) AS count
FROM orders
WHERE created_at >= date('now', :days || ' days')
GROUP BY date(created_at) ORDER BY date
```

**channel_distribution:** GROUP BY source.

**conversion_funnel:** 4 отдельных COUNT.

**ltv:** AVG + медиана через оконные функции.

**retention:** недельные когорты, обработка в Python после SQL.

**forecast:** линейная регрессия через sklearn (опционально).

## 4. Опциональные зависимости

```toml
[project.optional-dependencies]
analytics = ["pandas", "matplotlib", "scikit-learn"]
```

- Если sklearn не установлен → `forecast_orders()` возвращает null
- Если matplotlib не установлен → CLI `--output png` возвращает ошибку
- Graceful degradation — никаких падений

## 5. CLI-команды

```python
def register(app: typer.Typer):
    """Аналитика и статистика. Подкоманды в стиле config/db/plugin."""

    @app.command()
    def analytics_summary(
        output: str = typer.Option("text", "--output", "--out"),
    ): ...

    @app.command()
    def analytics_ltv(
        days: int = typer.Option(30, "--days", "-d"),
        output: str = typer.Option("text", "--output", "--out"),
    ): ...

    @app.command()
    def analytics_forecast(
        days: int = typer.Option(30, "--days", "-d"),
        output: str = typer.Option("text", "--output", "--out"),
    ): ...

    @app.command()
    def analytics_funnel(
        output: str = typer.Option("text", "--output", "--out"),
    ): ...
```

| Команда | --output | Примечание |
|---|---|---|
| `summary` | text, json | |
| `ltv` | text, json | png — отложено |
| `retention` | — | Отложено до 5.1. Не реализовывать CLI |
| `forecast` | text, json | png — отложено |
| `funnel` | text, json | |

## 6. Критерии приёмки

- `AnalyticsService.summary()` возвращает корректные счётчики
- `messages_over_time()` возвращает данные по дням
- `ltv()` считает средний/медианный LTV
- `forecast()` работает с sklearn, возвращает `[]` без него
- `retention()` — отложена до 5.1, не реализовывать
- CLI `ai-mini-box analytics summary` выводит таблицу
- CLI `ai-mini-box analytics ltv --output json` выводит JSON
- Никаких падений при отсутствии опциональных зависимостей
