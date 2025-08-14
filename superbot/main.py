"""Application entrypoint for Superbot."""

from __future__ import annotations

import asyncio
import signal
import sys
from pathlib import Path

import discord
from discord.ext import commands

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR / "src"))

from config import get_settings

from superbot.core.services.db import DB
from superbot.core.services.errors import register_global_error_handler
from superbot.core.services.logging_service import setup_logging
from superbot.loaders.cogs import load_all


async def main() -> None:
    """Run the Discord bot."""
    settings = get_settings()
    setup_logging(settings.log_level)
    await DB.init(settings.db_path)
    await DB.run_migrations()

    intents = discord.Intents.none()
    intents.guilds = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    register_global_error_handler(bot)
    await load_all(bot)

    loop = asyncio.get_running_loop()

    def _handle_shutdown() -> None:
        loop.create_task(bot.close())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _handle_shutdown)

    try:
        await bot.start(settings.discord_token)
    finally:
        await DB.close()


if __name__ == "__main__":
    asyncio.run(main())
