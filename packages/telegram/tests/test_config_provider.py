from pathlib import Path

from ai_mini_box.infrastructure.config import JsonConfigManager
from ai_mini_box_telegram.config_provider import TelegramConfigProvider


class TestTelegramConfigProvider:
    def _make_provider(self, tmp_path: Path) -> tuple[TelegramConfigProvider, JsonConfigManager]:
        cfg_path = tmp_path / "config.json"
        mgr = JsonConfigManager(str(cfg_path))
        provider = TelegramConfigProvider(config_path=str(cfg_path))
        return provider, mgr

    def test_get_config_masks_token(self, tmp_path: Path):
        provider, mgr = self._make_provider(tmp_path)
        mgr.set("telegram_token", "test:token")
        result = provider.get_config()
        assert result["telegram_token"] == "***"

    def test_get_config_returns_empty_when_no_token(self, tmp_path: Path):
        provider, mgr = self._make_provider(tmp_path)
        result = provider.get_config()
        assert result["telegram_token"] == ""

    def test_get_config_returns_poll_interval(self, tmp_path: Path):
        provider, mgr = self._make_provider(tmp_path)
        mgr.set("poll_interval", 60)
        result = provider.get_config()
        assert result["poll_interval"] == 60

    def test_set_config_saves_token(self, tmp_path: Path):
        provider, mgr = self._make_provider(tmp_path)
        result = provider.set_config({"telegram_token": "new:token"})
        assert result["success"] is True
        loaded = mgr.load()
        assert loaded.telegram_token == "new:token"

    def test_set_config_does_not_overwrite_token_with_mask(self, tmp_path: Path):
        provider, mgr = self._make_provider(tmp_path)
        mgr.set("telegram_token", "existing:token")
        result = provider.set_config({"telegram_token": "***"})
        assert result["success"] is True
        loaded = mgr.load()
        assert loaded.telegram_token == "existing:token"

    def test_set_config_updates_poll_interval(self, tmp_path: Path):
        provider, mgr = self._make_provider(tmp_path)
        mgr.set("poll_interval", 30)
        result = provider.set_config({"poll_interval": 60})
        assert result["success"] is True
        loaded = mgr.load()
        assert loaded.poll_interval == 60

    def test_set_config_handles_error(self, tmp_path: Path, mocker):
        provider, mgr = self._make_provider(tmp_path)
        mocker.patch(
            "ai_mini_box.infrastructure.config.JsonConfigManager.set",
            side_effect=ValueError("Invalid value"),
        )
        result = provider.set_config({"poll_interval": -1})
        assert result["success"] is False
        assert "Invalid value" in result["error"]

    def test_get_schema_contains_required_fields(self):
        provider = TelegramConfigProvider()
        schema = provider.get_schema()
        assert schema["title"] == "Telegram Bot Config"
        assert "telegram_token" in schema["properties"]
        assert schema["properties"]["telegram_token"]["secret"] is True
        assert schema["properties"]["poll_interval"]["default"] == 30
        assert schema["properties"]["poll_interval"]["minimum"] == 5
        assert schema["properties"]["poll_interval"]["maximum"] == 300
        assert "telegram_token" in schema["required"]

    def test_set_config_updates_allowed_chat_ids(self, tmp_path: Path):
        provider, mgr = self._make_provider(tmp_path)
        mgr.set("telegram_allowed_chat_ids", "[123]")
        result = provider.set_config({"telegram_allowed_chat_ids": [123, 456]})
        assert result["success"] is True
        loaded = mgr.load()
        assert loaded.telegram_allowed_chat_ids == [123, 456]

    def test_set_config_empty_token_does_not_overwrite(self, tmp_path: Path):
        provider, mgr = self._make_provider(tmp_path)
        mgr.set("telegram_token", "existing:token")
        result = provider.set_config({"telegram_token": ""})
        assert result["success"] is True
        loaded = mgr.load()
        assert loaded.telegram_token == "existing:token"

    def test_entry_point_registered(self):
        import importlib.metadata
        eps = importlib.metadata.entry_points(group="ai_mini_box.config_provider")
        telegram_eps = [ep for ep in eps if ep.name == "telegram"]
        assert len(telegram_eps) == 1, (
            f"Expected 1 telegram config_provider entry point, got {len(telegram_eps)}. "
            "Reinstall package: pip install -e packages/telegram"
        )
        provider = telegram_eps[0].load()
        assert isinstance(provider, TelegramConfigProvider)

    def test_get_config_defaults_when_file_missing(self, tmp_path: Path):
        cfg_path = tmp_path / "nonexistent" / "config.json"
        provider = TelegramConfigProvider(config_path=str(cfg_path))
        result = provider.get_config()
        assert result["telegram_token"] == ""
        assert result["poll_interval"] == 30
