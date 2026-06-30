from __future__ import annotations

import signal
import time

from loguru import logger

from ai_mini_box.core.services.registry import get_service


def run_daemon(interval: int = 60) -> None:
    running = True

    def _shutdown(sig, frame):
        nonlocal running
        logger.info("Received signal {}, shutting down...", sig)
        running = False

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, _shutdown)
        except (AttributeError, ValueError):
            pass

    logger.info("Process daemon started (interval={}s)", interval)

    while running:
        try:
            auto_processor = get_service("auto_processor")
            if auto_processor:
                total, assigned = auto_processor.process_all()
                logger.info("Checked {} messages, assigned {} to folders", total, assigned)
            else:
                logger.warning("AutoProcessor not registered")
        except Exception as e:
            logger.error("Process cycle failed: {}", e)

        for _ in range(interval):
            if not running:
                break
            time.sleep(1)

    logger.info("Process daemon stopped")
