# Spec 29 — Config Provider Protocol (web-dev)

## Goal

Переделать `PluginManager.get_plugin_config()` / `set_plugin_config()` так, чтобы для чтения конфига плагина он сначала пытался найти `ConfigProvider` (через core-механизм из spec 28), а если провайдера нет — падал бы на `data/config.json`.

## Зависимость

**Блокер:** Spec 28 (core-dev) должен быть завершён — нужен `get_config_provider(name)` из `ai_mini_box.core.services.config_provider`.

## Что меняется

### 1. `PluginManager.get_plugin_config(name)` — новая логика

```python
def get_plugin_config(self, name: str) -> dict | None:
    # 1. Пытаемся найти ConfigProvider
    try:
        from ai_mini_box.core.services.config_provider import get_config_provider
        provider = get_config_provider(name)
        if provider is not None:
            return provider.get_config()
    except Exception:
        pass  # fallback

    # 2. Fallback: старый путь через data/config.json
    if not self._CONFIG_PATH.exists():
        return None
    raw = json.loads(self._CONFIG_PATH.read_text(encoding="utf-8"))
    cfg = raw.get(name)
    if cfg and "email_password" in cfg:
        cfg = {**cfg, "email_password": "***"}
    return cfg
```

### 2. `PluginManager.set_plugin_config(name, body)` — новая логика

```python
def set_plugin_config(self, name: str, config: dict) -> dict:
    # 1. Пытаемся найти ConfigProvider
    try:
        from ai_mini_box.core.services.config_provider import get_config_provider
        provider = get_config_provider(name)
        if provider is not None:
            return provider.set_config(config)
    except Exception:
        pass  # fallback

    # 2. Fallback: старый путь
    # ... (существующий код)
```

### 3. `GET /{name}/config-schema` — через провайдера

```python
@router.get("/{name}/config-schema")
def get_plugin_config_schema(name: str):
    # 1. Через провайдера
    try:
        from ai_mini_box.core.services.config_provider import get_config_provider
        provider = get_config_provider(name)
        if provider is not None:
            return provider.get_schema()
    except Exception:
        pass

    # 2. Fallback: старый путь через module.config_schema()
    plugin = _manager.get_plugin(name)
    if plugin is None:
        raise HTTPException(404, detail=f"Plugin '{name}' not found")
    try:
        module_path = plugin["module"].split(":")[0]
        mod = importlib.import_module(module_path)
        if not hasattr(mod, "config_schema"):
            raise HTTPException(404, ...)
        return mod.config_schema()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=f"Error loading config schema: {e}")
```

### 4. Добавить `_manager` на те эндпоинты, где его нет

В `plugins.py` эндпоинт `GET /{name}/config-schema` (строка 90) не использует `_manager.config_schema()` — он сам импортирует модуль. Это дублирование. После перехода на провайдера — `get_plugin_config_schema` использует `try: provider.get_schema()`.

## Constraints

- **Никаких asyncio.** Всё синхронное.
- **Импорт провайдера — ленивый** (внутри функции, а не на уровне модуля). Плагин `ai-mini-box-core` не импортирует `ai_mini_box.core.services.config_provider` в глобальной области — только при вызове метода.
- **Ловить все Exception** в блоке провайдера. Если провайдер упал — падаем на fallback без ошибки.
- **Маскировка** остаётся на стороне провайдера. Для fallback (`data/config.json["email"]`) маскировка `email_password` сохраняется.

## Migration

После деплоя:
1. Если у плагина **нет** провайдера → поведение не меняется (fallback на `data/config.json`)
2. Если у плагина **есть** провайдер → конфиг читается через него
3. Пользователь ничего не замечает, 404 для LLM исчезает после реализации spec 30

## Acceptance Criteria

- [ ] `GET /api/plugins/llm/config` возвращает конфиг LLM (после реализации spec 30) — не 404
- [ ] `POST /api/plugins/llm/config` сохраняет конфиг LLM
- [ ] `GET /api/plugins/telegram/config` возвращает конфиг telegram (после реализации spec 31)
- [ ] `GET /api/plugins/llm/config-schema` возвращает JSON Schema
- [ ] `GET /api/plugins/nonexistent/config` → 404 (fallback: нет в data/config.json, нет провайдера)
- [ ] Старый `GET /api/plugins/email/config` продолжает работать через fallback
