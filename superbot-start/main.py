"""Entrypoint for the modular Discord bot.

Environment variables:
    BOT_TOKEN/TOKEN  Discord bot token (required)
    PREFIXES         Comma separated command prefixes (default '!')
    INTENTS          Comma separated intent names or 'all'
    COG_MODE         'manual' or 'auto' (default 'manual')
    COGS             Comma separated extension paths (manual mode)
    COGS_PATH        Base package for auto discovery (default 'minebot.cogs')
    LOG_LEVEL        Logging level (default 'INFO')
    LOG_FORMAT       Python logging format (optional)

To switch cog loading modes, set COG_MODE to 'manual' and list modules in
COGS, or set COG_MODE='auto' to discover all cogs under COGS_PATH.

Run locally:
    $ export BOT_TOKEN=...  # or TOKEN=...
    $ python main.py
"""
from __future__ import annotations

import asyncio
import logging
import signal

import discord
from discord.ext import commands

from helpers.config import Settings, load_settings
from helpers.errors import report
from helpers.loader import load_extensions
from helpers.logging import init_logger


async def on_startup(bot: commands.Bot, settings: Settings, logger: logging.Logger) -> None:
    """Hook executed before the bot connects to Discord."""
    logger.info("starting with cog mode '%s'", settings.cog_mode)


async def on_shutdown(bot: commands.Bot, settings: Settings, logger: logging.Logger) -> None:
    """Hook executed after the bot disconnects."""
    logger.info("shutdown complete")


def build_bot(settings: Settings) -> commands.Bot:
    """Create and configure the bot instance."""
    bot = commands.Bot(command_prefix=settings.prefixes, intents=settings.intents, help_command=None)
    bot.settings = settings  # type: ignore[attr-defined]
    return bot


async def start_bot(bot: commands.Bot, settings: Settings, logger: logging.Logger) -> None:
    """Load extensions and start the bot."""
    await on_startup(bot, settings, logger)
    try:
        await load_extensions(bot, settings, logger)
        await bot.start(settings.token)
    finally:
        await on_shutdown(bot, settings, logger)


def main() -> None:
    """Load settings, configure logging, and run the bot."""
    settings = load_settings()
    logger = init_logger(settings)
    bot = build_bot(settings)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    stop_event = asyncio.Event()

    async def runner() -> None:
        try:
            await start_bot(bot, settings, logger)
        except Exception as exc:  # pragma: no cover - top-level error
            report(exc, "runner")
        finally:
            stop_event.set()

    def _request_shutdown() -> None:
        if not stop_event.is_set():
            logger.info("shutdown signal received")
            loop.create_task(bot.close())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _request_shutdown)

    loop.create_task(runner())
    try:
        loop.run_until_complete(stop_event.wait())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


if __name__ == "__main__":
    main()
