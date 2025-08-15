"""Entry point for Superbot."""

from __future__ import annotations

import asyncio
import platform
import signal
import sys
import time
from pathlib import Path

import discord
from discord.ext import commands

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))

from config import get_settings
from superbot.core.services.db import DBService
from superbot.core.services.errors import setup_error_handlers
from superbot.core.services.logging_service import (
    log_error,
    log_info,
    log_warning,
    setup_logging,
    uptime_tracker,
)
from superbot.core.utils.time import format_timedelta
from superbot.loaders import cogs as cog_loader


async def run() -> None:
    settings = get_settings()
    setup_logging()
    await DBService.init()

    intents = discord.Intents.all()
    missing: list[str] = []
    if not intents.message_content:
        missing.append("message_content")
    if missing:
        log_warning("Missing intents: %s", ", ".join(missing))

    bot = commands.Bot(
        command_prefix=settings.COMMAND_PREFIX,
        intents=intents,
    )

    setup_error_handlers(bot)

    start = time.perf_counter()
    loaded, failed = await cog_loader.load_all(bot)
    elapsed = time.perf_counter() - start
    log_info(
        "Cogs loaded: %s succeeded, %s failed in %.2fs",
        len(loaded),
        len(failed),
        elapsed,
    )

    @bot.event
    async def on_ready() -> None:
        banner = (
            "✅ Superbot online\n"
            f"Python: {platform.python_version()} | discord.py: {discord.__version__}\n"
            f"Guilds: {len(bot.guilds)} | Cogs: {len(bot.cogs)}/{len(loaded)+len(failed)}\n"
            f"Uptime: {format_timedelta(uptime_tracker.uptime())}"
        )
        log_info(banner.replace("\n", " | "))
        if settings.STARTUP_CHANNEL_ID:
            channel = bot.get_channel(settings.STARTUP_CHANNEL_ID)
            if channel:
                await channel.send(banner)
        log_info(
            "READY – cogs=%s/%s guilds=%s",
            len(bot.cogs),
            len(loaded) + len(failed),
            len(bot.guilds),
        )

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(bot.close()))

    try:
        await bot.start(settings.DISCORD_TOKEN)
    finally:
        await DBService.close()


def main() -> None:
    try:
        asyncio.run(run())
    except Exception:  # noqa: BLE001
        log_error("Fatal error during startup", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
