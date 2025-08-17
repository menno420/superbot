"""Utilities for managing bot extensions."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from time import perf_counter

from discord.ext import commands

logger = logging.getLogger("superbot")


def is_loaded(bot: commands.Bot, name: str) -> bool:
    """Return True if the extension is currently loaded."""
    return name in bot.extensions


def list_loaded(bot: commands.Bot) -> list[str]:
    """List the names of loaded extensions."""
    return sorted(bot.extensions.keys())


async def load_one(bot: commands.Bot, name: str) -> None:
    """Load a single extension if not already loaded."""
    if is_loaded(bot, name):
        return
    try:
        await bot.load_extension(name)
        logger.info("loaded %s", name)
    except Exception as exc:  # noqa: BLE001
        logger.exception("failed to load %s", name, exc_info=exc)


async def unload_one(bot: commands.Bot, name: str) -> None:
    """Unload a loaded extension."""
    if not is_loaded(bot, name):
        return
    try:
        await bot.unload_extension(name)
        logger.info("unloaded %s", name)
    except Exception as exc:  # noqa: BLE001
        logger.exception("failed to unload %s", name, exc_info=exc)


async def reload_one(bot: commands.Bot, name: str) -> None:
    """Reload an extension, loading it first if needed."""
    if not is_loaded(bot, name):
        await load_one(bot, name)
        return
    try:
        await bot.reload_extension(name)
        logger.info("reloaded %s", name)
    except Exception as exc:  # noqa: BLE001
        logger.exception("failed to reload %s", name, exc_info=exc)


async def load_all_cogs(bot: commands.Bot, names: Iterable[str]) -> None:
    """Attempt to load all provided extensions and log a summary."""
    start = perf_counter()
    success = 0
    failed = 0
    for name in names:
        if is_loaded(bot, name):
            continue
        try:
            await bot.load_extension(name)
            logger.info("loaded %s", name)
            success += 1
        except Exception as exc:  # noqa: BLE001
            logger.exception("failed to load %s", name, exc_info=exc)
            failed += 1
    duration = perf_counter() - start
    logger.info(
        "Cogs loaded: %s succeeded, %s failed in %.2fs",
        success,
        failed,
        duration,
    )
