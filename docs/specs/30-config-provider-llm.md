# Spec 30 — LlmConfigProvider (llm-dev)

## Goal

Реализовать `ConfigProvider` для LLM-плагина, чтобы веб-интерфейс мог читать и изменять конфиг LLM через единый протокол.

## Зависимость

**Блокер:** Spec 28 (core-dev) — должен быть определён `ConfigProvider` protocol.

## Что сделать

### 1. Создать `LlmConfigProvider` в `ai_mini_box_llm/plugin.py`

```python
class LlmConfigProvider:
    """ConfigProvider для LLM-плагина.

    Читает/пишет конфиг через LlmConfig (data/llm_config.json).
    """

    def get_config(self) -> dict:
        from .config import LlmConfig
        cfg = LlmConfig.load()
        return {
            "provider": cfg.provider,
            "model_path": cfg.model_path or "",
            "embeddings_model": cfg.embeddings_model or "all-MiniLM-L6-v2",
            "rag_enabled": cfg.rag_enabled,
            "rag_top_k": cfg.rag_top_k,
            "confidence_min": cfg.confidence_min,
            "batch_size": cfg.batch_size,
        }

    def set_config(self, config: dict) -> dict:
        from .config import LlmConfig
        cfg = LlmConfig.load()

        # Merge — обновляем только переданные поля
        for key in ("provider", "model_path", "embeddings_model", "rag_top_k", "confidence_min", "batch_size"):
            if key in config:
                setattr(cfg, key, config[key])

        # rag_enabled — bool special case
        if "rag_enabled" in config:
            cfg.rag_enabled = bool(config["rag_enabled"])

        cfg.save()
        return {"success": True}

    def get_schema(self) -> dict:
        return {
            "$schema": "https://json-schemas.org/draft/2020-12/schema",
            "type": "object",
            "title": "LLM Plugin Config",
            "properties": {
                "provider": {
                    "type": "string",
                    "title": "Провайдер",
                    "enum": ["local", "remote"],
                    "default": "local",
                },
                "model_path": {
                    "type": "string",
                    "title": "Путь к модели",
                    "default": "",
                },
                "embeddings_model": {
                    "type": "string",
                    "title": "Embeddings модель",
                    "default": "all-MiniLM-L6-v2",
                },
                "rag_enabled": {
                    "type": "boolean",
                    "title": "RAG включён",
                    "default": False,
                },
                "rag_top_k": {
                    "type": "integer",
                    "title": "RAG top-K",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 20,
                },
                "confidence_min": {
                    "type": "number",
                    "title": "Мин.置信ence для шаблона",
                    "default": 0.6,
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
                "batch_size": {
                    "type": "integer",
                    "title": "Размер батча для обучения",
                    "default": 50,
                    "minimum": 10,
                },
            },
            "required": [],
        }

# Экспорт для entry point
config_provider = LlmConfigProvider()
```

### 2. Зарегистрировать entry point в `pyproject.toml`

```toml
[project.entry-points."ai_mini_box.config_provider"]
llm = "ai_mini_box_llm.plugin:config_provider"
```

### 3. Обновить `docs/specs/27-llm-core-rewrite.md` (если актуально)

Добавить ссылку на spec 30 в секции шагов.

## Что НЕ нужно делать

- **Не менять** `LlmConfig` — он уже работает.
- **Не менять** `data/llm_config.json` — формат остаётся прежним.
- **Не импортировать** `ai_mini_box.core.services.config_provider` — проверка типа не нужна на уровне плагина.
- **Не удалять** старую функцию `config_schema()` — она остаётся для обратной совместимости (fallback в web).

## Эффект

После деплоя spec 29 (web-dev) + spec 30:
- `GET /api/plugins/llm/config` → JSON с полями LLM-конфига (вместо 404)
- `POST /api/plugins/llm/config` → сохраняет в `data/llm_config.json`
- `GET /api/plugins/llm/config-schema` → JSON Schema для построения формы в вебе

## Acceptance Criteria

- [ ] `LlmConfigProvider.get_config()` возвращает все поля из `LlmConfig`
- [ ] `LlmConfigProvider.set_config({"rag_top_k": 5})` обновляет только rag_top_k, остальное не трогает
- [ ] `LlmConfigProvider.set_config({"rag_enabled": True})` корректно сохраняет булево значение
- [ ] `LlmConfigProvider.get_schema()` возвращает валидную JSON Schema
- [ ] Entry point `ai_mini_box.config_provider` зарегистрирован и читается через `importlib.metadata.entry_points(group="ai_mini_box.config_provider")`
- [ ] `data/llm_config.json` создаётся/обновляется после `set_config()`
