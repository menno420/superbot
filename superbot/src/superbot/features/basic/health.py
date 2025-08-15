"""Health check command."""

from __future__ import annotations

import logging
import platform

import discord
from discord import app_commands
from discord.ext import commands

from ...core.services.db import DBService
from ...core.services.logging_service import uptime_tracker
from ...core.utils.time import format_timedelta


class Health(commands.Cog):
    """Expose a simple health slash command."""

    def __init__(self, bot: commands.Bot) -> None:
        """Store bot reference."""
        self.bot = bot

    @app_commands.command(name="health", description="Show bot health information.")
    async def health(self, interaction: discord.Interaction) -> None:
        """Return bot health information."""
        db_ok = True
        last_versions: list[str] = []
        try:
            rows = await DBService.fetch_all(
                "SELECT version FROM schema_version ORDER BY version DESC LIMIT 3",
            )
            last_versions = [str(r["version"]) for r in rows]
            await DBService.fetch_one("SELECT 1")
        except Exception:  # noqa: BLE001
            db_ok = False
        uptime = format_timedelta(uptime_tracker.uptime())
        guilds = len(self.bot.guilds)
        users = sum(g.member_count or 0 for g in self.bot.guilds)
        migrations = ", ".join(last_versions) if last_versions else "none"
        message = (
            f"Uptime: {uptime}\n"
            f"Python: {platform.python_version()} | discord.py: {discord.__version__}\n"
            f"Guilds: {guilds} | Users: {users}\n"
            f"Cogs loaded: {len(self.bot.cogs)}\n"
            f"DB: {'OK' if db_ok else 'FAIL'} | Migrations: {migrations}\n"
            f"Log level: {logging.getLevelName(logging.getLogger().level)}\n"
            f"Ready: {'✅' if self.bot.is_ready() else '❌'}"
        )
        await interaction.response.send_message(message, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    """Load the health cog."""
    await bot.add_cog(Health(bot))
