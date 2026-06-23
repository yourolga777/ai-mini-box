import json
from unittest.mock import MagicMock

from ai_mini_box_telegram.update_checker import check_pypi_update, warn_updates


class TestCheckPypiUpdate:
    def _mock_urlopen(self, mocker, version_str: str):
        mock_resp = MagicMock()
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.read.return_value = json.dumps({"info": {"version": version_str}})
        mocker.patch("urllib.request.urlopen", return_value=mock_resp)

    def test_returns_latest_when_newer(self, mocker):
        mocker.patch(
            "ai_mini_box_telegram.update_checker.version", return_value="0.1.0"
        )
        self._mock_urlopen(mocker, "0.2.0")
        assert check_pypi_update("ai-mini-box-telegram") == "0.2.0"

    def test_returns_none_when_same_version(self, mocker):
        mocker.patch(
            "ai_mini_box_telegram.update_checker.version", return_value="0.1.0"
        )
        self._mock_urlopen(mocker, "0.1.0")
        assert check_pypi_update("ai-mini-box-telegram") is None

    def test_returns_none_on_network_error(self, mocker):
        mocker.patch(
            "ai_mini_box_telegram.update_checker.version", return_value="0.1.0"
        )
        mocker.patch("urllib.request.urlopen", side_effect=OSError("timeout"))
        assert check_pypi_update("ai-mini-box-telegram") is None

    def test_returns_none_on_package_not_found(self, mocker):
        mocker.patch(
            "ai_mini_box_telegram.update_checker.version", side_effect=Exception("not found")
        )
        assert check_pypi_update("nonexistent") is None


class TestWarnUpdates:
    def _mock_urlopen(self, mocker, version_str: str):
        mock_resp = MagicMock()
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.read.return_value = json.dumps({"info": {"version": version_str}})
        mocker.patch("urllib.request.urlopen", return_value=mock_resp)

    def test_logs_warning_when_update_available(self, mocker):
        mocker.patch(
            "ai_mini_box_telegram.update_checker.version", return_value="0.1.0"
        )
        self._mock_urlopen(mocker, "0.2.0")
        logger_warning = mocker.patch("loguru.logger.warning")

        warn_updates("ai-mini-box-telegram")

        logger_warning.assert_called_once()
        args = logger_warning.call_args
        assert "0.1.0" in str(args)
        assert "0.2.0" in str(args)

    def test_no_warning_when_up_to_date(self, mocker):
        mocker.patch(
            "ai_mini_box_telegram.update_checker.version", return_value="0.1.0"
        )
        self._mock_urlopen(mocker, "0.1.0")
        logger_warning = mocker.patch("loguru.logger.warning")

        warn_updates("ai-mini-box-telegram")

        logger_warning.assert_not_called()
