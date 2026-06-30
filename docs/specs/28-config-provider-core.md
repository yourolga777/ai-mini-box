# Spec 28 — Config Provider Protocol (core-dev)

## Goal

Определить протокол `ConfigProvider` в core, чтобы любой плагин мог единообразно expose свой конфиг в веб-интерфейс, не используя `data/config.json`.

## Motivation

- `PluginManager.get_plugin_config(name)` жёстко зашит на чтение `data/config.json[name]`
- LLM-плагин хранит конфиг в отдельном `data/llm_config.json` — веб выдаёт 404
- У каждого плагина свой способ хранения конфига, нет стандарта
- Веб-интерфейс (PluginDetail.tsx) зовёт `GET /api/plugins/{name}/config` и ожидает JSON — неважно, откуда он берётся

## Deliverables

1. Файл `packages/core/ai_mini_box/core/services/config_provider.py`
2. Entry point group `ai_mini_box.config_provider` — регистрируется в core
3. Функция `get_config_provider(name) -> ConfigProvider | None` — поиск провайдера по entry point
4. Функция `discover_config_providers() -> dict[str, ConfigProvider]` — все зарегистрированные провайдеры

## Protocol

```python
# ai_mini_box/core/services/config_provider.py

from __future__ import annotations
from typing import Protocol, runtime_checkable


@runtime_checkable
class ConfigProvider(Protocol):
    """Протокол провайдера конфига для плагина.

    Каждый плагин может зарегистрировать свою реализацию через entry point
    `ai_mini_box.config_provider`. Если провайдер не зарегистрирован,
    PluginManager использует fallback на data/config.json.
    """

    def get_config(self) -> dict:
        """Вернуть текущий конфиг плагина как плоский dict.
        Значения могут быть любого JSON-типа.
        Чувствительные поля (пароли, токены) должны быть маскированы ("***").
        """

    def set_config(self, config: dict) -> dict:
        """Сохранить конфиг плагина.
        Принимает dict с полями для обновления (merge, не полная замена).
        Возвращает {"success": True} или {"success": False, "error": "..."}.
        """

    def get_schema(self) -> dict:
        """Вернуть JSON Schema для конфига плагина.
        Формат: https://json-schema.org/understanding-json-schema/
        Используется веб-интерфейсом для построения формы.
        """
```

### Entry point registration

Core добавляет entry point group `ai_mini_box.config_provider` в систему. Регистрация происходит стандартно через `importlib.metadata.entry_points()`:

```python
def get_config_provider(name: str) -> ConfigProvider | None:
    """Найти ConfigProvider по имени плагина через entry points."""
    for ep in importlib.metadata.entry_points(group="ai_mini_box.config_provider"):
        if ep.name == name:
            provider = ep.load()
            if isinstance(provider, ConfigProvider):
                return provider
    return None


def discover_config_providers() -> dict[str, ConfigProvider]:
    """Вернуть словарь {name: provider} для всех зарегистрированных провайдеров."""
    result: dict[str, ConfigProvider] = {}
    for ep in importlib.metadata.entry_points(group="ai_mini_box.config_provider"):
        try:
            provider = ep.load()
            if isinstance(provider, ConfigProvider):
                result[ep.name] = provider
        except Exception:
            continue
    return result
```

## Constraints

- **Никакой зависимости от web.** Core не может импортировать `ai_mini_box_web`. Протокол использует только stdlib + typing.
- **Никаких asyncio.** Core синхронный.
- **Минимальная сложность.** Protocol из typing + importlib — без датаклассов, без Pydantic.
- **Плагин без провайдера не ломается.** Если entry point не найден или загрузить не удалось — возвращается `None`, web использует fallback.
- **Маскировка секретов.** `get_config()` должен маскировать чувствительные поля на стороне плагина. Core/web не знают, какие поля чувствительны.

## Impact

- **Затрагивает только** `packages/core/ai_mini_box/core/services/` — новый файл, без изменений существующего кода
- **Обратная совместимость:** полная. Старый `PluginManager.get_plugin_config()` продолжает работать как fallback
- **Плагины:** могут добавлять config provider без изменения core

## Acceptance Criteria

- [ ] `ConfigProvider` протокол определён в `ai_mini_box/core/services/config_provider.py`
- [ ] `get_config_provider("nonexistent")` возвращает `None` (не падает)
- [ ] `discover_config_providers()` возвращает пустой `{}` если ни один плагин не зарегистрировал провайдера
- [ ] Entry point `ai_mini_box.config_provider` существует и читается через `importlib.metadata.entry_points()`
- [ ] Тест: мок-провайдер регистрируется через entry point → `get_config_provider("mock")` возвращает его
