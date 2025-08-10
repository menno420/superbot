from __future__ import annotations

import logging
from typing import Any


def report(exc: BaseException, context: str = "") -> None:
    """Report an unexpected exception using the configured logger."""
    logger = logging.getLogger("bot")
    logger.error("Unhandled exception in %s", context, exc_info=exc)
