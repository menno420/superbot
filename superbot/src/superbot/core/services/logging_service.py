"""Logging configuration and utilities."""

from __future__ import annotations

import asyncio
import logging
import logging.handlers
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import aiohttp

from config import get_settings


class UptimeTracker:
    """Track application start time and uptime."""

    def __init__(self) -> None:
        """Record the start time."""
        self.start = datetime.now(tz=timezone.utc)

    def uptime(self) -> timedelta:
        """Return the uptime."""
        return datetime.now(tz=timezone.utc) - self.start


uptime_tracker = UptimeTracker()


class DiscordWebhookHandler(logging.Handler):
    """Logging handler that forwards records to a Discord webhook."""

    def __init__(self, url: str) -> None:
        """Initialize the handler."""
        super().__init__()
        self.url = url

    async def _post(self, message: str) -> None:
        async with aiohttp.ClientSession() as session:
            from contextlib import suppress
            with suppress(Exception):
                await session.post(self.url, json={"content": message[:2000]})

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401
        """Send log record to webhook."""
        message = self.format(record)
        asyncio.create_task(self._post(message))


def setup_logging() -> logging.Logger:
    """Configure root logger with console and file handlers."""
    settings = get_settings()
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers
    for handler in list(root.handlers):
        root.removeHandler(handler)

    formatter = logging.Formatter(
        "timestamp=%(asctime)s level=%(levelname)s name=%(name)s message=%(message)s",
        "%Y-%m-%dT%H:%M:%SZ",
    )
    formatter.converter = time.gmtime  # type: ignore[name-defined]

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    log_file = Path(settings.LOG_DIR) / "bot.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5,
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    if settings.LOG_WEBHOOK_URL:
        webhook = DiscordWebhookHandler(settings.LOG_WEBHOOK_URL)
        webhook.setFormatter(formatter)
        root.addHandler(webhook)

    return root


def log_debug(msg: str, *args: object, **kwargs: object) -> None:
    """Log a debug message."""
    logging.getLogger().debug(msg, *args, **kwargs)


def log_info(msg: str, *args: object, **kwargs: object) -> None:
    """Log an info message."""
    logging.getLogger().info(msg, *args, **kwargs)


def log_warning(msg: str, *args: object, **kwargs: object) -> None:
    """Log a warning message."""
    logging.getLogger().warning(msg, *args, **kwargs)


def log_error(msg: str, *args: object, **kwargs: object) -> None:
    """Log an error message."""
    logging.getLogger().error(msg, *args, **kwargs)
