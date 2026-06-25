# Провайдеры LLM

## Локальный провайдер (local)

Использует `llama-cpp-python` для запуска GGUF-моделей на CPU.

**Плюсы:** работает офлайн, бесплатно, данные не уходят.
**Минусы:** требует ресурсов CPU/RAM.

```json
{
  "provider": "local",
  "model_path": "data/models/model.gguf",
  "n_ctx": 4096,
  "n_threads": 4
}
```

## Удалённый провайдер (remote)

Использует OpenAI API или любой совместимый сервис (Ollama, LM Studio, vLLM).

**Плюсы:** не нагружает локальную машину.
**Минусы:** требует интернета, может быть платным.

```json
{
  "provider": "remote",
  "api_url": "https://api.openai.com/v1",
  "api_key": "sk-...",
  "model_name": "gpt-3.5-turbo"
}
```

Для Ollama:
```json
{
  "provider": "remote",
  "api_url": "http://localhost:11434/v1",
  "api_key": "ollama",
  "model_name": "llama3.2"
}
```

## RAG (Retrieval-Augmented Generation)

Добавляет контекст из базы знаний к генерации ответов.

```json
{
  "rag_enabled": true,
  "rag_top_k": 3
}
```

После включения выполните: `ai-mini-box llm ingest-kb`
