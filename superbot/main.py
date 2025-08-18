# ruff: noqa: D100

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import discord
from discord.ext import commands

# Ensure src package on path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from superbot.config import Settings  # noqa: E402
from superbot.core.services.db import init_db  # noqa: E402
from superbot.core.services.errors import report  # noqa: E402
from superbot.core.services.logging_service import init_logging  # noqa: E402
from superbot.loaders import cogs as cog_loader  # noqa: E402


async def start_bot() -> None:
    """Initialize services, load cogs, and run the bot."""
    settings = Settings()
    logger = init_logging(settings.log_level)
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(
        command_prefix=settings.command_prefix,
        intents=intents,
        help_command=None,
    )
    bot.settings = settings
    bot.logger = logger

    @bot.event
    async def on_error(
        event: str,
        *_args: object,
        **_kwargs: object,
    ) -> None:  # noqa: ANN401
        """Log errors from events with their traceback."""
        logger.exception("Unhandled event %s", event)

    @bot.event
    async def on_ready() -> None:
        """Log startup and optionally announce in a channel."""
        logger.info("startup complete")
        if settings.startup_channel_id:
            channel = bot.get_channel(settings.startup_channel_id)
            if channel:
                await channel.send("Bot started")

    async with bot:
        await init_db(settings.db_path)
        await cog_loader.load_all_cogs(bot, settings.preload_cogs)
        if settings.guild_ids:
            for gid in settings.guild_ids:
                cmds = await bot.tree.sync(guild=discord.Object(id=gid))
                logger.info("synced %s commands", len(cmds), extra={"guild": gid})
        else:
            cmds = await bot.tree.sync()
            logger.info("synced %s global commands", len(cmds))
        await bot.start(settings.discord_token)


def main() -> None:
    """Run the bot's asynchronous entrypoint."""
    try:
        asyncio.run(start_bot())
    except Exception as exc:  # pragma: no cover
        report(exc, "main")


if __name__ == "__main__":
    main()
