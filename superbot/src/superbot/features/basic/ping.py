"""Ping command cog."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from ...core.services.db import DBService


class Ping(commands.Cog):
    """Provide latency checks."""

    def __init__(self, bot: commands.Bot) -> None:
        """Store the bot instance."""
        self.bot = bot

    @commands.hybrid_command(name="ping", description="Show bot latency.")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def ping(self, ctx: commands.Context) -> None:
        """Reply with bot latency and database status."""
        latency = self.bot.latency * 1000
        db_ok = True
        try:
            await DBService.fetch_one("SELECT 1")
        except Exception:  # noqa: BLE001
            db_ok = False
        await ctx.reply(
            f"Pong! {latency:.0f}ms | DB {'OK' if db_ok else 'FAIL'}",
            mention_author=False,
        )

    @app_commands.command(name="ping", description="Show bot latency.")
    @app_commands.checks.cooldown(1, 1, key=lambda i: i.user.id)
    async def ping_slash(self, interaction: discord.Interaction) -> None:
        """Slash command variant of ping."""
        latency = self.bot.latency * 1000
        db_ok = True
        try:
            await DBService.fetch_one("SELECT 1")
        except Exception:  # noqa: BLE001
            db_ok = False
        await interaction.response.send_message(
            f"Pong! {latency:.0f}ms | DB {'OK' if db_ok else 'FAIL'}",
        )


async def setup(bot: commands.Bot) -> None:
    """Load the ping cog."""
    await bot.add_cog(Ping(bot))
