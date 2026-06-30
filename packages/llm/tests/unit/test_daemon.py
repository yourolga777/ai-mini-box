from __future__ import annotations

import signal
from unittest.mock import MagicMock, patch

import pytest

from ai_mini_box_llm.daemon import run_daemon


class TestRunDaemon:
    def test_loop_calls_process_all(self):
        mock_processor = MagicMock()
        mock_processor.process_all.return_value = (5, 2)
        with patch("ai_mini_box_llm.daemon.get_service", return_value=mock_processor):
            with patch("ai_mini_box_llm.daemon.time.sleep", side_effect=StopIteration):
                with pytest.raises(StopIteration):
                    run_daemon(interval=1)
        mock_processor.process_all.assert_called_once()

    def test_loop_continues_on_exception(self):
        mock_processor = MagicMock()
        mock_processor.process_all.side_effect = [ValueError("test error"), (0, 0), StopIteration]
        with patch("ai_mini_box_llm.daemon.get_service", return_value=mock_processor):
            with patch("ai_mini_box_llm.daemon.time.sleep", side_effect=[None, None, StopIteration]):
                with pytest.raises(StopIteration):
                    run_daemon(interval=1)
        assert mock_processor.process_all.call_count >= 2

    def test_no_auto_processor_logs_warning(self):
        with patch("ai_mini_box_llm.daemon.get_service", return_value=None):
            with patch("ai_mini_box_llm.daemon.time.sleep", side_effect=StopIteration):
                with patch("ai_mini_box_llm.daemon.logger.warning") as mock_warn:
                    with pytest.raises(StopIteration):
                        run_daemon(interval=1)
                    mock_warn.assert_called_once_with("AutoProcessor not registered")

    def test_signal_registers_handler(self):
        handlers = {}

        def fake_signal(sig, handler):
            handlers[sig] = handler

        mock_processor = MagicMock()
        mock_processor.process_all.return_value = (0, 0)
        with patch("ai_mini_box_llm.daemon.get_service", return_value=mock_processor):
            with patch("ai_mini_box_llm.daemon.signal.signal", fake_signal):
                with patch("ai_mini_box_llm.daemon.time.sleep", side_effect=StopIteration):
                    with pytest.raises(StopIteration):
                        run_daemon(interval=1)
        assert signal.SIGTERM in handlers
        assert signal.SIGINT in handlers

    def test_signal_register_failure_doesnt_crash(self):
        mock_processor = MagicMock()
        mock_processor.process_all.return_value = (0, 0)
        with patch("ai_mini_box_llm.daemon.get_service", return_value=mock_processor):
            with patch("ai_mini_box_llm.daemon.signal.signal", side_effect=ValueError("bad signal")):
                with patch("ai_mini_box_llm.daemon.time.sleep", side_effect=StopIteration):
                    with pytest.raises(StopIteration):
                        run_daemon(interval=1)
