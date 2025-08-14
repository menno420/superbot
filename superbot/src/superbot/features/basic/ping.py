"""Basic ping command cog."""

from __future__ import annotations

import logging
import os

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)


class Ping(commands.Cog):
    """Provide a basic latency check command."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the cog."""
        self.bot = bot

    @app_commands.command(name="ping", description="Return bot latency.")
    async def ping(self, interaction: discord.Interaction) -> None:
        """Respond with bot latency and environment name."""
        latency_ms = self.bot.latency * 1000
        env_name = os.getenv("ENV_NAME", "development")
        logger.info("Ping invoked by %s", interaction.user)
        await interaction.response.send_message(
            f"Pong! {latency_ms:.0f}ms | {env_name}",
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    """Load the ping cog."""
    await bot.add_cog(Ping(bot))
