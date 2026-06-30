import json
from pathlib import Path

from ai_mini_box_telegram.config import TelegramPluginConfig


class TestTelegramPluginConfig:
    def test_creates_file_on_first_access(self, tmp_path: Path):
        path = tmp_path / "telegram_config.json"
        cfg = TelegramPluginConfig(str(path))
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["api_base_url"] == "https://api.telegram.org/bot"
        assert data["request_timeout"] == 10
        assert data["poll_interval"] == 2

    def test_default_properties(self, tmp_path: Path):
        cfg = TelegramPluginConfig(str(tmp_path / "cfg.json"))
        assert cfg.api_base_url == "https://api.telegram.org/bot"
        assert cfg.request_timeout == 10
        assert cfg.poll_interval == 2

    def test_set_and_get(self, tmp_path: Path):
        cfg = TelegramPluginConfig(str(tmp_path / "cfg.json"))
        cfg.set("api_base_url", "https://custom.api.com/bot")
        cfg2 = TelegramPluginConfig(str(tmp_path / "cfg.json"))
        assert cfg2.api_base_url == "https://custom.api.com/bot"

    def test_set_poll_interval(self, tmp_path: Path):
        cfg = TelegramPluginConfig(str(tmp_path / "cfg.json"))
        cfg.set("poll_interval", 5)
        assert cfg.poll_interval == 5

    def test_returns_defaults_on_corrupted_file(self, tmp_path: Path):
        cfg_path = tmp_path / "cfg.json"
        cfg_path.write_text("{invalid", encoding="utf-8")
        cfg = TelegramPluginConfig(str(cfg_path))
        assert cfg.api_base_url == "https://api.telegram.org/bot"
        assert cfg.request_timeout == 10
        assert cfg.poll_interval == 2

    def test_atomic_write(self, tmp_path: Path):
        cfg_path = tmp_path / "cfg.json"
        cfg = TelegramPluginConfig(str(cfg_path))
        cfg.set("poll_interval", 7)
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        assert data["poll_interval"] == 7
        assert not cfg_path.with_suffix(".tmp").exists()

    def test_all_returns_copy(self, tmp_path: Path):
        cfg = TelegramPluginConfig(str(tmp_path / "cfg.json"))
        data = cfg.all()
        data["poll_interval"] = 99
        assert cfg.poll_interval == 2
