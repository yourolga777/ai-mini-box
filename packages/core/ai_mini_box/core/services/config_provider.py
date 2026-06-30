from __future__ import annotations

import importlib.metadata
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


_GROUP = "ai_mini_box.config_provider"


def get_config_provider(name: str) -> ConfigProvider | None:
    """Найти ConfigProvider по имени плагина через entry points."""
    for ep in importlib.metadata.entry_points(group=_GROUP):
        if ep.name == name:
            try:
                provider = ep.load()
                if isinstance(provider, ConfigProvider):
                    return provider
            except Exception:
                return None
    return None


def discover_config_providers() -> dict[str, ConfigProvider]:
    """Вернуть словарь {name: provider} для всех зарегистрированных провайдеров."""
    result: dict[str, ConfigProvider] = {}
    for ep in importlib.metadata.entry_points(group=_GROUP):
        try:
            provider = ep.load()
            if isinstance(provider, ConfigProvider):
                result[ep.name] = provider
        except Exception:
            continue
    return result
