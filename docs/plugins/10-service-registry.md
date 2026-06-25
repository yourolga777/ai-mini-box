# Service Registry

The service registry lets plugins register and discover each other's functionality. This decouples plugins — one plugin provides a service, another consumes it, neither imports the other directly.

## How it works

```python
from ai_mini_box.core.services.registry import register_service, get_service

# Register (in your plugin's register() function)
register_service("my_service", my_instance)

# Discover (anywhere, any plugin)
service = get_service("my_service")
if service:
    service.do_something()
```

The registry is a global dict — simple, transparent, no magic.

## When to use

| Scenario | Example |
|---|---|
| LLM provider | One plugin provides LLM, all others consume |
| Notifications | Central notifier, any plugin can send alerts |
| Speech/text processing | TTS, STT plugins |
| Payment gateway | Shared payment processing |

## Contract pattern

For a well-defined service contract, define an ABC in core (`ai_mini_box.core.services`) that both provider and consumer import:

```python
# core defines the contract (ai_mini_box/core/services/llm.py)
from abc import ABC, abstractmethod

class LlmService(ABC):
    @abstractmethod
    def classify(self, text: str) -> str | None: ...
    @abstractmethod
    def draft_response(self, text: str) -> str | None: ...
```

```python
# Plugin A (LLM provider) implements the contract
from ai_mini_box.core.services.registry import register_service
from ai_mini_box.core.services.llm import LlmService

class MyLlm(LlmService):
    def classify(self, text): ...
    def draft_response(self, text): ...

def register(app: typer.Typer):
    register_service("llm", MyLlm())
```

```python
# Plugin B (consumer) uses it
from ai_mini_box.core.services.registry import get_service

llm = get_service("llm")
if llm:
    topic = llm.classify("How much is this?")
else:
    topic = "fallback: no LLM available"
```

## Available service contracts

| Service name | Contract class | Provided by | Status |
|---|---|---|---|
| `"llm"` | `LlmService` | `ai-mini-box-llm` | Planned |

## Testing with the registry

```python
from ai_mini_box.core.services.registry import register_service, get_service

# Register a mock in tests
class MockLlm:
    def classify(self, text): return "test_topic"

register_service("llm", MockLlm())

# Your code under test
service = get_service("llm")
assert service.classify("hello") == "test_topic"
```

## Best practices

- **Register early** — call `register_service()` at the top of your `register()` function
- **Check before use** — always do `if service:` before calling
- **Null Object pattern** — providers should register a real implementation; consumers get `None` if not available
- **Don't overuse** — for simple CLI commands and direct DB access, import core directly, not via registry
- **Thread safety** — the registry is a simple dict; writes happen at startup (single-threaded), reads happen at runtime (multi-threaded). As long as all `register_service` calls finish before daemons start, it's safe.
