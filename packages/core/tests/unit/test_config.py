import json
from pathlib import Path

import pytest

from ai_mini_box.infrastructure.config import AppConfig, JsonConfigManager, SENSITIVE_FIELDS


@pytest.fixture
def tmp_manager(tmp_path: Path) -> JsonConfigManager:
    return JsonConfigManager(tmp_path / "config.json")


def test_load_defaults(tmp_manager):
    config = tmp_manager.load()
    assert config.telegram_token == ""
    assert config.poll_interval == 30


def test_save_and_load(tmp_manager):
    config = tmp_manager.load()
    config.poll_interval = 60
    tmp_manager.save(config)

    loaded = tmp_manager.load()
    assert loaded.poll_interval == 60


def test_set_str_field(tmp_manager):
    tmp_manager.set("email_login", "test@example.com")
    config = tmp_manager.load()
    assert config.email_login == "test@example.com"


def test_set_int_field(tmp_manager):
    tmp_manager.set("poll_interval", "60")
    config = tmp_manager.load()
    assert config.poll_interval == 60
    assert isinstance(config.poll_interval, int)


def test_set_bool_field(tmp_manager):
    tmp_manager.set("notification_on_order", "false")
    config = tmp_manager.load()
    assert config.notification_on_order is False


def test_set_list_field_from_json(tmp_manager):
    tmp_manager.set("telegram_allowed_chat_ids", "[1, 2, 3]")
    config = tmp_manager.load()
    assert config.telegram_allowed_chat_ids == [1, 2, 3]


def test_set_list_field_from_comma(tmp_manager):
    tmp_manager.set("telegram_allowed_chat_ids", "10, 20, 30")
    config = tmp_manager.load()
    assert config.telegram_allowed_chat_ids == [10, 20, 30]


def test_set_sensitive_encrypts(tmp_manager):
    tmp_manager.set("telegram_token", "secret-token-123")
    with open(tmp_manager.path, encoding="utf-8") as f:
        raw = json.load(f)
    assert raw["telegram_token"] != "secret-token-123"
    assert raw["telegram_token"] != ""


def test_set_invalid_type(tmp_manager):
    with pytest.raises(ValueError, match="must be an integer"):
        tmp_manager.set("poll_interval", "not-a-number")


def test_set_unknown_key(tmp_manager):
    with pytest.raises(ValueError, match="Unknown config key"):
        tmp_manager.set("nonexistent", "value")


def test_unset_field(tmp_manager):
    tmp_manager.set("email_imap_server", "custom.server.com")
    assert tmp_manager.unset("email_imap_server") is True
    config = tmp_manager.load()
    assert config.email_imap_server == "imap.yandex.ru"


def test_unset_unknown_key(tmp_manager):
    with pytest.raises(ValueError, match="Unknown config key"):
        tmp_manager.unset("nonexistent")


def test_unset_not_in_file(tmp_manager):
    result = tmp_manager.unset("email_imap_server")
    assert result is False


def test_encrypt_decrypt_roundtrip(tmp_manager):
    tmp_manager.set("telegram_token", "my-token")
    config = tmp_manager.load()
    assert config.telegram_token == "my-token"


def test_sensitive_fields_constant():
    assert "telegram_token" in SENSITIVE_FIELDS
    assert "email_password" in SENSITIVE_FIELDS
    assert "poll_interval" not in SENSITIVE_FIELDS


def test_guess_section():
    assert AppConfig.guess_section("telegram_token") == "Telegram"
    assert AppConfig.guess_section("email_imap_server") == "Email"
    assert AppConfig.guess_section("poll_interval") == "General"
