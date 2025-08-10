from __future__ import annotations

import logging
from typing import Optional

from .config import Settings


def init_logger(settings: Settings) -> logging.Logger:
    """Configure and return the root logger."""
    logger = logging.getLogger("bot")
    if logger.handlers:
        return logger
    level = getattr(logging, settings.log_level, logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(settings.log_format))
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger
