"""Centralized error reporting."""

from __future__ import annotations

import logging


def report(exc: BaseException, context: str = "") -> None:
    """Log an unexpected exception."""
    logger = logging.getLogger("superbot")
    logger.error("Unhandled exception in %s", context, exc_info=exc)
