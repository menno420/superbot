"""Logging service for the bot."""

from __future__ import annotations

import logging


def init_logging(level: str) -> logging.Logger:
    """Configure and return the application logger."""
    logger = logging.getLogger("superbot")
    if logger.handlers:
        return logger
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logger
