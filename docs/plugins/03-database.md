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
| `repos.messages` | Message | `list()`, `get_by_id()`, `add()`, `search()` |
| `repos.orders` | Order | `list()`, `get_by_id()`, `add()`, `update()` |

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

## Custom queries

If you need custom SQL, use SQLAlchemy directly:

```python
from sqlalchemy import text

with get_db() as session:
    result = session.execute(text("SELECT count(*) FROM contacts"))
    count = result.scalar()
```

## Entity models

| Model | Key fields |
|---|---|
| `Contact` | `id`, `name`, `phone`, `email`, `telegram`, `source` |
| `Product` | `id`, `name`, `price` (int, kopecks) |
| `Message` | `id`, `text`, `source`, `topic`, `contact_id`, `chat_id` |
| `Order` | `id`, `status`, `items`, `total`, `contact_id` |

## Enums

```python
from ai_mini_box.core.models import (
    MessageSource,   # TELEGRAM, EMAIL, WHATSAPP, SMS, MANUAL
    Topic,           # PRICES, ORDER, COMPLAINT, SCHEDULE, OTHER
    OrderStatus,     # NEW, PROCESSING, COMPLETED, CANCELLED
)
```
