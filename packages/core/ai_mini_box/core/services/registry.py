from typing import Any

_REGISTRY: dict[str, Any] = {}


def register_service(name: str, instance: Any) -> None:
    _REGISTRY[name] = instance


def get_service(name: str) -> Any | None:
    return _REGISTRY.get(name)


def unregister_service(name: str) -> None:
    _REGISTRY.pop(name, None)


def list_services() -> list[str]:
    return list(_REGISTRY.keys())
