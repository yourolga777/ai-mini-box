from unittest.mock import MagicMock, patch

import pytest

from ai_mini_box.core.services.config_provider import (
    ConfigProvider,
    discover_config_providers,
    get_config_provider,
)


class MockConfigProvider:
    """Test double that satisfies ConfigProvider protocol."""

    def get_config(self) -> dict:
        return {"api_key": "***", "model": "gpt-4"}

    def set_config(self, config: dict) -> dict:
        return {"success": True}

    def get_schema(self) -> dict:
        return {"type": "object", "properties": {"api_key": {"type": "string"}}}


class NonProvider:
    """Класс, не удовлетворяющий ConfigProvider."""
    pass


def _make_entry_point(name: str, provider):
    ep = MagicMock()
    ep.name = name
    ep.load.return_value = provider
    return ep


def test_get_provider_found():
    ep = _make_entry_point("mock", MockConfigProvider())
    with patch("ai_mini_box.core.services.config_provider.importlib.metadata.entry_points", return_value=[ep]):
        provider = get_config_provider("mock")
        assert provider is not None
        assert provider.get_config()["model"] == "gpt-4"


def test_get_provider_not_found():
    with patch("ai_mini_box.core.services.config_provider.importlib.metadata.entry_points", return_value=[]):
        provider = get_config_provider("nonexistent")
        assert provider is None


def test_get_provider_wrong_name():
    ep = _make_entry_point("other", MockConfigProvider())
    with patch("ai_mini_box.core.services.config_provider.importlib.metadata.entry_points", return_value=[ep]):
        provider = get_config_provider("mock")
        assert provider is None


def test_get_provider_non_protocol():
    """Провайдер, не реализующий протокол, не возвращается."""
    ep = _make_entry_point("bad", NonProvider())
    with patch("ai_mini_box.core.services.config_provider.importlib.metadata.entry_points", return_value=[ep]):
        provider = get_config_provider("bad")
        assert provider is None


def test_get_provider_load_error():
    """Ошибка загрузки entry point возвращает None."""
    ep = MagicMock()
    ep.name = "broken"
    ep.load.side_effect = ImportError("no module")
    with patch("ai_mini_box.core.services.config_provider.importlib.metadata.entry_points", return_value=[ep]):
        provider = get_config_provider("broken")
        assert provider is None


def test_discover_empty():
    with patch("ai_mini_box.core.services.config_provider.importlib.metadata.entry_points", return_value=[]):
        result = discover_config_providers()
        assert result == {}


def test_discover_multiple():
    ep1 = _make_entry_point("mock1", MockConfigProvider())
    ep2 = _make_entry_point("mock2", MockConfigProvider())
    with patch("ai_mini_box.core.services.config_provider.importlib.metadata.entry_points", return_value=[ep1, ep2]):
        result = discover_config_providers()
        assert len(result) == 2
        assert "mock1" in result
        assert "mock2" in result


def test_discover_skips_non_protocol():
    ep1 = _make_entry_point("good", MockConfigProvider())
    ep2 = _make_entry_point("bad", NonProvider())
    with patch("ai_mini_box.core.services.config_provider.importlib.metadata.entry_points", return_value=[ep1, ep2]):
        result = discover_config_providers()
        assert "good" in result
        assert "bad" not in result


def test_discover_skips_load_error():
    """Ошибка загрузки не ломает discover."""
    good = _make_entry_point("good", MockConfigProvider())
    broken = MagicMock()
    broken.name = "broken"
    broken.load.side_effect = ImportError("no module")

    with patch("ai_mini_box.core.services.config_provider.importlib.metadata.entry_points", return_value=[broken, good]):
        result = discover_config_providers()
        assert "good" in result
        assert "broken" not in result


def test_provider_schema():
    provider = MockConfigProvider()
    schema = provider.get_schema()
    assert "properties" in schema
    assert schema["properties"]["api_key"]["type"] == "string"


def test_provider_get_config_returns_dict():
    provider = MockConfigProvider()
    cfg = provider.get_config()
    assert isinstance(cfg, dict)
    assert cfg["api_key"] == "***"
