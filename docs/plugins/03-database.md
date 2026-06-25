# Database Access

Use the core's database layer instead of raw SQL. This ensures compatibility with future database backends and proper transaction handling.

## Getting a session

```python
from ai_mini_box.infrastructure.database import get_db
from ai_mini_box.core.container import RepoContainer

# Context manager — auto-commit on success, rollback on error
with get_db() as session:
    repos = RepoContainer(session)
    # ... work with repos ...
```

## Available repositories

| Repository | Entity | Methods |
|---|---|---|
| `repos.contacts` | Contact | `list()`, `get_by_id()`, `add()`, `update()`, `delete()`, `search()` |
| `repos.products` | Product | `list()`, `get_by_id()`, `add()`, `update()`, `delete()`, `search()` |
| `repos.messages` | Message | `list()`, `get_by_id()`, `add()`, `update()`, `search()` |
| `repos.orders` | Order | `list()`, `get_by_id()`, `add()`, `update()` |
| `repos.tasks` | Task | `list()`, `get_by_id()`, `add()`, `update()`, `delete()`, `query()` |
| `repos.kb` | KnowledgeBaseItem | `list()`, `get_by_id()`, `add()`, `update()`, `delete()`, `search_by_topic()`, `find_matching()` |

All methods work with Pydantic v2 models from `ai_mini_box.core.models`.

## List with filters

```python
# All contacts
repos.contacts.list()

# With pagination
repos.contacts.list(limit=10, offset=0)

# Sorted
repos.contacts.list(sort="name")

# Filtered by field (exact match)
repos.contacts.list(telegram="123456")

# Search (name or phone or email)
repos.contacts.search("Alice")
```

## QueryBuilder — chainable query helper

Every repository has a `query()` method that returns a `QueryBuilder` for complex in-memory filtering:

```python
# chained filter
results = repos.tasks.query().filter(status="pending", priority=TaskPriority.HIGH).all()

# filter + search + sort
results = repos.contacts.query() \
    .filter(telegram__isnot=None) \
    .search("Alice", "name", "phone") \
    .sort("name") \
    .limit(10) \
    .all()

# count
count = repos.tasks.query().filter(status="done").count()

# first match
task = repos.products.query().search("widget", "name").first()
```

Available chain methods:
| Method | Purpose |
|---|---|
| `.filter(**kwargs)` | Exact field match (ignores None) |
| `.search(query, *fields)` | Case-insensitive substring match |
| `.sort(key, reverse=False)` | Sort by field |
| `.limit(n)` | First n items |
| `.offset(n)` | Skip n items |
| `.all()` | Return full list |
| `.first()` | Return first or None |
| `.count()` | Return count |

## Create a record

```python
from ai_mini_box.core.models import Contact, MessageSource

contact = Contact(
    name="Alice",
    phone="+123456789",
    telegram="12345",
    source=MessageSource.MANUAL,
)
created = repos.contacts.add(contact)
```

With `get_db()` auto-commit, you don't need to call `session.commit()`.

## Custom queries

If you need custom SQL, use SQLAlchemy directly:

```python
from sqlalchemy import text

with get_db() as session:
    result = session.execute(text("SELECT count(*) FROM contacts"))
    count = result.scalar()
```

## Migrations: adding tables safely

If your plugin needs new tables, add a migration file in `core/migrations/versions/`. **Always guard `create_table`** against already-existing tables — `Base.metadata.create_all()` at server startup creates them first:

```python
# migrations/versions/abc123_add_my_table.py
import sqlalchemy as sa
from alembic import op

def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'my_table' not in inspector.get_table_names():
        op.create_table('my_table',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('name', sa.String(), nullable=False),
        )
```

Alternatively, if your plugin needs completely separate tables, use its own SQLite file rather than adding to core's migration chain.

## Entity models

| Model | Key fields |
|---|---|
| `Contact` | `id`, `name`, `phone`, `email`, `telegram`, `source`, `total_spent` |
| `Product` | `id`, `name`, `price_kopecks` (int), `stock`, `unit`, `category` |
| `Message` | `id`, `text`, `source`, `topic`, `contact_id`, `chat_id`, `draft_response`, `extracted_phone`, `extracted_name` |
| `Order` | `id`, `status`, `total_kopecks`, `contact_id`, `source_message_id` |
| `Task` | `id`, `title`, `description`, `due_date`, `due_time`, `priority` (TaskPriority), `status`, `contact_id`, `assignee` |
| `KnowledgeBaseItem` | `id`, `topic`, `question_keywords` (list[str]), `answer_text` |

## KnowledgeBase — matching logic

`find_matching(text, topic)` returns KB entries whose `question_keywords` intersect with words in the text. Results sorted by match count descending.

```python
matches = repos.kb.find_matching("How much is delivery?", topic=Topic.ORDER)
if matches:
    typer.echo(matches[0].answer_text)
```

## State persistence

For plugins that need to keep track of cursors, offsets, or checkpoint state between restarts, store a JSON file in the `data/` directory:

```python
from pathlib import Path
import json


class FileOffsetRepo:
    def __init__(self, path: str = "data/my_plugin_state.json"):
        self._path = Path(path)

    def get_offset(self) -> int | None:
        if not self._path.exists():
            return None
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return data.get("offset")
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def save_offset(self, offset: int) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps({"offset": offset}), encoding="utf-8")
```

This pattern is used by the Telegram plugin (`FileTelegramStateRepo`) to persist `update_id` offset between polls.

## Enums

```python
from ai_mini_box.core.models import (
    MessageSource,   # TELEGRAM, EMAIL, WHATSAPP, SMS, MANUAL
    Topic,           # PRICES, ORDER, COMPLAINT, SCHEDULE, OTHER
    OrderStatus,     # NEW, PROCESSING, COMPLETED, CANCELLED
    TaskPriority,    # LOW, MEDIUM, HIGH
)
```
