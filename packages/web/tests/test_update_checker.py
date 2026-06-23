import json
from unittest.mock import MagicMock

from ai_mini_box_web.services.update_checker import check_pypi_update, warn_updates


class TestCheckPypiUpdate:
    def _mock_urlopen(self, mocker, version_str: str):
        mock_resp = MagicMock()
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.read.return_value = json.dumps({"info": {"version": version_str}})
        mocker.patch("urllib.request.urlopen", return_value=mock_resp)

    def test_returns_latest_when_newer(self, mocker):
        mocker.patch(
            "ai_mini_box_web.services.update_checker.version", return_value="0.1.0"
        )
        self._mock_urlopen(mocker, "0.2.0")
        assert check_pypi_update("ai-mini-box-web") == "0.2.0"

    def test_returns_none_when_same_version(self, mocker):
        mocker.patch(
            "ai_mini_box_web.services.update_checker.version", return_value="0.1.0"
        )
        self._mock_urlopen(mocker, "0.1.0")
        assert check_pypi_update("ai-mini-box-web") is None

    def test_returns_none_on_network_error(self, mocker):
        mocker.patch(
            "ai_mini_box_web.services.update_checker.version", return_value="0.1.0"
        )
        mocker.patch("urllib.request.urlopen", side_effect=OSError("timeout"))
        assert check_pypi_update("ai-mini-box-web") is None

    def test_returns_none_on_package_not_found(self, mocker):
        mocker.patch("importlib.metadata.version", side_effect=Exception("not found"))
        assert check_pypi_update("nonexistent") is None


class TestWarnUpdates:
    def _mock_urlopen(self, mocker, version_str: str):
        mock_resp = MagicMock()
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.read.return_value = json.dumps({"info": {"version": version_str}})
        mocker.patch("urllib.request.urlopen", return_value=mock_resp)

    def test_logs_warning_when_update_available(self, mocker):
        mocker.patch(
            "ai_mini_box_web.services.update_checker.version", return_value="0.1.0"
        )
        self._mock_urlopen(mocker, "0.2.0")
        logger_warning = mocker.patch("loguru.logger.warning")

        warn_updates("ai-mini-box-web")

        logger_warning.assert_called_once()
        args = logger_warning.call_args
        assert "0.1.0" in str(args)
        assert "0.2.0" in str(args)

    def test_no_warning_when_up_to_date(self, mocker):
        mocker.patch(
            "ai_mini_box_web.services.update_checker.version", return_value="0.1.0"
        )
        self._mock_urlopen(mocker, "0.1.0")
        logger_warning = mocker.patch("loguru.logger.warning")

        warn_updates("ai-mini-box-web")

        logger_warning.assert_not_called()

    def test_multiple_packages(self, mocker):
        mocker.patch(
            "ai_mini_box_web.services.update_checker.version", return_value="0.1.0"
        )

        def side_effect(*args, **kwargs):
            mock_resp = MagicMock()
            mock_resp.__enter__.return_value = mock_resp
            url = str(args[0])
            if "core" in url:
                mock_resp.read.return_value = json.dumps({"info": {"version": "0.2.0"}})
            else:
                mock_resp.read.return_value = json.dumps({"info": {"version": "0.1.0"}})
            return mock_resp

        mocker.patch("urllib.request.urlopen", side_effect=side_effect)
        logger_warning = mocker.patch("loguru.logger.warning")

        warn_updates("ai-mini-box-core", "ai-mini-box-web")

        assert logger_warning.call_count == 1
