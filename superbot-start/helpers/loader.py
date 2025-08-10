from __future__ import annotations

import asyncio
import importlib
import pkgutil
import logging
from typing import List

from .config import Settings


def discover_extensions(base_package: str) -> List[str]:
    package = importlib.import_module(base_package)
    return [f"{base_package}.{name}" for _, name, _ in pkgutil.walk_packages(package.__path__)]


async def _load_with_retry(bot, ext: str, settings: Settings, logger: logging.Logger) -> None:
    for attempt in range(1, settings.reload_retries + 1):
        try:
            await asyncio.wait_for(bot.load_extension(ext), timeout=settings.cog_timeout)
        except Exception as exc:
            logger.exception("Failed to load %s (attempt %s)", ext, attempt, exc_info=exc)
            if attempt < settings.reload_retries:
                await asyncio.sleep(1)
        else:
            logger.info("Loaded %s", ext)
            return
    logger.error("Giving up on %s", ext)


async def load_extensions(bot, settings: Settings, logger: logging.Logger) -> None:
    if settings.cog_mode == "manual":
        extensions = settings.cogs
    else:
        extensions = discover_extensions(settings.cogs_path)
    for ext in extensions:
        await _load_with_retry(bot, ext, settings, logger)
