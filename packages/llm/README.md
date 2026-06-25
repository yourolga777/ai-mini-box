# ai-mini-box-llm

LLM plugin for [ai-mini-box-core](https://github.com/Kibertum/ai-mini-box) — adds natural language processing: message classification, response drafting, entity extraction, and RAG.

## Features

- **Classify** messages by topic (Prices, Order, Complaint, Schedule, Other)
- **Draft** auto-responses to customer messages
- **Extract** entities (phone, name, address, date, order ID)
- **RAG** — Retrieval-Augmented Generation from Knowledge Base
- **Two providers**: local (GGUF via llama-cpp-python) or remote (OpenAI API)
- **CLI commands** for status, testing, model download, KB indexing

## Installation

```bash
pip install ai-mini-box-llm[local]   # local inference
pip install ai-mini-box-llm[remote]  # OpenAI API
```

## Configuration

Config file: `data/llm_config.json` (auto-created with defaults):

```json
{
  "provider": "local",
  "model_path": "data/models/Phi-3-mini-q4.gguf",
  "n_ctx": 4096,
  "n_threads": 4,
  "rag_enabled": false,
  "rag_top_k": 3
}
```

## Usage

```bash
# Show status
ai-mini-box llm status

# Classify a message
ai-mini-box llm classify "сколько стоит доставка?"

# Generate a draft response
ai-mini-box llm draft "хочу заказать пиццу" --topic "Заказ"

# Extract entities
ai-mini-box llm extract "Позвоните Ивану по телефону +7 123 456 78 90"

# Download a model
ai-mini-box llm download-model Qwen/Qwen2.5-0.5B-Instruct-GGUF:q4_0

# Rebuild RAG index
ai-mini-box llm ingest-kb
```

## Architecture

The plugin registers an `LlmService` implementation via the generic service registry:

```python
from ai_mini_box.core.services.registry import register_service, get_service

# Registration (done by plugin automatically)
register_service("llm", MyLlmService())

# Usage by any other module
llm = get_service("llm")
if llm:
    topic = llm.classify("How much?")
```

When the plugin is not installed, `get_service("llm")` returns `None`, and the core falls back to built-in heuristics (KeywordClassifier, regex extraction).

## Requirements

- Python 3.12+
- ai-mini-box-core >= 5.0.0
- Optional: llama-cpp-python, openai, huggingface-hub
