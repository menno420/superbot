"""Logging configuration service."""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def setup_logging(level: str | int) -> logging.Logger:
    """Configure and return the application root logger.

    Args:
        level: Logging level as name or integer.

    Returns:
        Configured root logger.
    """
    log_level = logging.getLevelName(level) if isinstance(level, str) else level
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    project_root = Path(__file__).resolve().parents[4]
    log_file = project_root / "data" / "logs" / "app.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=3,
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    return root_logger
