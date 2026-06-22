from pathlib import Path

from loguru import logger

from ai_mini_box.infrastructure.logger import setup_logging


def test_setup_logging_console_only():
    setup_logging(verbose=False)
    logger.info("console only — should not raise")


def test_setup_logging_creates_file(tmp_path):
    log_file = tmp_path / "test.log"
    setup_logging(verbose=True, log_file=log_file)
    logger.info("test message")
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "test message" in content


def test_setup_logging_custom_path(tmp_path):
    log_file = tmp_path / "logs" / "app.log"
    setup_logging(log_file=log_file)
    logger.info("custom path test")
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "custom path test" in content
