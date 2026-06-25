# LLM Plugin Specification

This document is the contract for the developer building `ai-mini-box-llm` — a plugin that provides LLM-powered intelligence to the entire ecosystem.

## Purpose

The LLM plugin replaces the built-in fallback heuristics (keyword classification, regex extraction) with actual LLM inference. All other plugins and the core itself use the LLM via the service registry — they don't import this plugin directly.

## What the LLM does

Three core tasks:

| Task | Input | Output | Replaces |
|---|---|---|---|
| **Classify** | Message text | `Topic` enum | `KeywordClassifier` in `classifier.py` |
| **Draft response** | Message text + topic | Answer text (or None) | Layer 2 placeholder in `answer_service.py` |
| **Extract entities** | Message text | `dict` with phone, name, order_id, address, date | Regex `extract_phone()` in `extraction.py` |

## Entry point

```toml
[project.entry-points."ai_mini_box.tools"]
llm = "ai_mini_box_llm.plugin:register"

[project.entry-points."ai_mini_box.help"]
llm = "ai_mini_box_llm"
```

## Contract: LlmService

Implement `LlmService` ABC from `ai_mini_box.core.services.llm`:

```python
from ai_mini_box.core.models import Topic
from ai_mini_box.core.services.llm import LlmService

class MyLlmService(LlmService):
    def classify(self, text: str) -> Topic | None:
        """Return Topic enum or None if uncertain."""
        ...

    def draft_response(self, text: str, topic: Topic | None = None) -> str | None:
        """Generate a draft reply. Return None if can't generate."""
        ...

    def extract_entities(self, text: str) -> dict:
        """Return dict with keys: phone, name, order_id, address, date.
        Missing keys should be absent (not None)."""
        ...
```

## NullLlmService (built into core)

When the LLM plugin is NOT installed, `get_service("llm")` returns `None`. Core falls back to:
- `KeywordClassifier` for classification
- `extract_phone()` regex for phone extraction
- KB-only `auto_draft_response()` (Layer 1, no generation)

Your plugin replaces these with real LLM inference.

## How to register

```python
# ai_mini_box_llm/plugin.py
import typer
from ai_mini_box.core.services.registry import register_service

def register(app: typer.Typer):
    # 1. Register LLM service — happens before any daemon starts
    from .service import MyLlmService
    register_service("llm", MyLlmService())

    # 2. Register CLI commands
    llm_app = typer.Typer(help="LLM commands")
    app.add_typer(llm_app, name="llm")

    @llm_app.command()
    def status():
        """Show LLM model status."""
        typer.echo("LLM plugin active")
```

## Two provider modes

Support both, selected by config:

### Local (default)

```toml
# pyproject.toml
[project.optional-dependencies]
local = ["llama-cpp-python>=0.2"]
```

- Loads GGUF model from `config.llm_model_path`
- CPU inference via `llama_cpp.Llama`
- Minimal dependencies, works offline

### Remote

```toml
[project.optional-dependencies]
remote = ["openai>=1.0"]
```

- Connects to any OpenAI-compatible API
- Config: `llm_api_url`, `llm_api_key`, `llm_model_name`
- Can use: OpenAI, Ollama, LM Studio, vLLM, etc.

## Config fields (add to plugin's own config file)

Don't extend `AppConfig`. Use a separate config file:

```python
import json
from pathlib import Path

class LlmConfig:
    def __init__(self, path="data/llm_config.json"):
        self.path = Path(path)

    def load(self) -> dict:
        if not self.path.exists():
            return {"provider": "local", "model_path": "models/model.gguf"}
        return json.loads(self.path.read_text(encoding="utf-8"))
```

Suggested fields:
| Field | Type | Default | Description |
|---|---|---|---|
| `provider` | `str` | `"local"` | `"local"` or `"remote"` |
| `model_path` | `str` | `"models/model.gguf"` | Path to GGUF (local) |
| `n_ctx` | `int` | `4096` | Context size (local) |
| `n_threads` | `int` | `4` | CPU threads (local) |
| `api_url` | `str` | `""` | API base URL (remote) |
| `api_key` | `str` | `""` | API key (remote) |
| `model_name` | `str` | `""` | Model name (remote) |

## How other plugins use it

```python
from ai_mini_box.core.services.registry import get_service

llm = get_service("llm")
if llm:
    topic = llm.classify("How much is delivery?")
    draft = llm.draft_response("How much is delivery?", topic=topic)
    entities = llm.extract_entities("Call me at +7 123 456 78 90")
```

## Testing

### Unit tests with mock

```python
from ai_mini_box.core.services.registry import register_service
from ai_mini_box.testing import MockContactRepo

class MockLlm:
    def classify(self, text): return Topic.PRICES
    def draft_response(self, text, topic=None): return "This is a draft"
    def extract_entities(self, text): return {"phone": "+7 123 456 78 90"}

def test_with_llm():
    register_service("llm", MockLlm())
    # ... test your logic that uses LLM
```

### Integration tests

Run with a tiny GGUF model (e.g., Qwen2.5-0.5B-Q4) in CI, or mock the LLM calls entirely.

## Package structure

```
ai-mini-box-llm/
├── pyproject.toml
├── README.md
├── ai_mini_box_llm/
│   ├── __init__.py
│   ├── plugin.py        # register() — entry point
│   ├── service.py       # LlmService implementation
│   ├── config.py        # LlmConfig
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── local.py     # llama-cpp-python
│   │   └── remote.py    # OpenAI-compatible API
│   ├── prompt.py        # Prompt templates
│   └── help/
│       00-installation.md
│       01-commands.md
│       02-providers.md
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   └── test_service.py
│   └── integration/
│       └── test_local.py
```

## What NOT to do

- ❌ Don't import ai_mini_box.core.classifier_llm — that's the old built-in, to be deprecated
- ❌ Don't modify core code — your plugin registers via the registry, no core changes needed
- ❌ Don't add LLM fields to AppConfig — use your own config file
- ❌ Don't hardcode model path — use config
