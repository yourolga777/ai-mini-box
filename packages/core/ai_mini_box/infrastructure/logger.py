import sys
from pathlib import Path
from typing import Optional

from loguru import logger


def setup_logging(verbose: bool = False, log_file: Optional[Path] = None):
    logger.remove()
    level = "DEBUG" if verbose else "INFO"
    logger.add(sys.stdout, format="{time:HH:mm:ss} | {level:<7} | {message}", level=level)

    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            str(log_file),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level:<7} | {name}:{function}:{line} | {message}",
            level="DEBUG",
            rotation="1 MB",
            retention=3,
        )
    return logger
