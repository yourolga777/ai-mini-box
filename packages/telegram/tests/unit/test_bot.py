import pytest
import requests

from ai_mini_box_telegram.bot import TelegramBot
from ai_mini_box_telegram.exceptions import TelegramAPIError


class TestTelegramBot:
    def test_get_updates_returns_list(self, mocker):
        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {"ok": True, "result": [{"update_id": 1}]}
        mock_resp.raise_for_status.return_value = None
        mocker.patch("requests.get", return_value=mock_resp)

        bot = TelegramBot("test:token")
        result = bot.get_updates()

        assert result == [{"update_id": 1}]

    def test_get_updates_passes_offset(self, mocker):
        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {"ok": True, "result": []}
        mock_resp.raise_for_status.return_value = None
        get = mocker.patch("requests.get", return_value=mock_resp)

        bot = TelegramBot("test:token")
        bot.get_updates(offset=42)

        call_kwargs = get.call_args[1]
        assert call_kwargs["params"]["offset"] == 42

    def test_get_updates_raises_on_api_error(self, mocker):
        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {"ok": False, "description": "Bad token"}
        mock_resp.raise_for_status.return_value = None
        mocker.patch("requests.get", return_value=mock_resp)

        bot = TelegramBot("bad:token")
        with pytest.raises(TelegramAPIError, match="Bad token"):
            bot.get_updates()

    def test_get_updates_raises_on_network_error(self, mocker):
        mocker.patch("requests.get", side_effect=requests.ConnectionError("connection failed"))

        bot = TelegramBot("test:token")
        with pytest.raises(TelegramAPIError, match="connection failed"):
            bot.get_updates()

    def test_send_message_returns_true_on_success(self, mocker):
        mock_resp = mocker.Mock()
        mock_resp.ok = True
        mocker.patch("requests.post", return_value=mock_resp)

        bot = TelegramBot("test:token")
        assert bot.send_message(chat_id=123, text="Hello") is True

    def test_send_message_returns_false_on_failure(self, mocker):
        mock_resp = mocker.Mock()
        mock_resp.ok = False
        mocker.patch("requests.post", return_value=mock_resp)

        bot = TelegramBot("test:token")
        assert bot.send_message(chat_id=123, text="Hello") is False

    def test_send_message_returns_false_on_network_error(self, mocker):
        mocker.patch("requests.post", side_effect=requests.ConnectionError("fail"))

        bot = TelegramBot("test:token")
        assert bot.send_message(chat_id=123, text="Hello") is False
