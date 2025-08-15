"""Administrative commands."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from config import get_settings
from ...core.services.db import DBService
from ...core.services.logging_service import log_info
from ...loaders import cogs as cog_loader

settings = get_settings()


def is_owner(interaction: discord.Interaction) -> bool:
    """Return True if the user is an owner."""
    return interaction.user.id in settings.OWNER_IDS


def owner_only() -> app_commands.Check:
    """Check decorator for owner-only commands."""
    return app_commands.check(is_owner)


async def cog_name_autocomplete(
    _: discord.Interaction, current: str,
) -> list[app_commands.Choice[str]]:
    """Autocomplete helper for cog names."""
    names = cog_loader.discover_cogs()
    return [
        app_commands.Choice(name=n, value=n)
        for n in names
        if current.lower() in n.lower()
    ]

class Admin(commands.Cog):
    """Admin slash commands."""

    def __init__(self, bot: commands.Bot) -> None:
        """Store the bot instance."""
        self.bot = bot

    # ------------------------------------------------------------------
    @owner_only()
    @app_commands.command(name="restart", description="Restart the bot.")
    async def restart(self, interaction: discord.Interaction) -> None:
        """Restart the bot process."""
        await interaction.response.send_message("Restarting...", ephemeral=True)
        log_info("Restart requested by %s", interaction.user.id)
        await DBService.close()
        os.execv(sys.executable, [sys.executable] + sys.argv)  # noqa: S606

    # ------------------------------------------------------------------
    @owner_only()
    @app_commands.command(name="sync", description="Sync slash commands.")
    @app_commands.describe(guild="Guild ID to sync to")
    async def sync(
        self, interaction: discord.Interaction, guild: discord.Object | None = None,
    ) -> None:
        """Sync slash commands to guilds or globally."""
        if guild:
            self.bot.tree.copy_global_to(guild=guild)
            synced = await self.bot.tree.sync(guild=guild)
            await interaction.response.send_message(
                f"Synced {len(synced)} commands to guild {guild.id}", ephemeral=True,
            )
            return
        if settings.GUILD_IDS:
            total = 0
            for gid in settings.GUILD_IDS:
                g = discord.Object(id=gid)
                self.bot.tree.copy_global_to(guild=g)
                total += len(await self.bot.tree.sync(guild=g))
            await interaction.response.send_message(
                f"Synced {total} commands to {len(settings.GUILD_IDS)} guilds",
                ephemeral=True,
            )
        else:
            synced = await self.bot.tree.sync()
            await interaction.response.send_message(
                f"Globally synced {len(synced)} commands", ephemeral=True,
            )

    # ------------------------------------------------------------------
    cogs = app_commands.Group(name="cogs", description="Cog management")

    @cogs.command(name="list", description="List available cogs")
    @owner_only()
    async def cogs_list(self, interaction: discord.Interaction) -> None:
        """List loaded and unloaded cogs."""
        available = cog_loader.discover_cogs()
        loaded = [n for n in available if n in self.bot.extensions]
        unloaded = [n for n in available if n not in self.bot.extensions]
        message = (
            f"Loaded: {', '.join(loaded) if loaded else 'none'}\n"
            f"Unloaded: {', '.join(unloaded) if unloaded else 'none'}"
        )
        await interaction.response.send_message(message, ephemeral=True)

    @cogs.command(name="reload", description="Reload a cog")
    @owner_only()
    @app_commands.autocomplete(name=cog_name_autocomplete)
    async def cogs_reload(self, interaction: discord.Interaction, name: str) -> None:
        """Reload a cog."""
        ok, err = await cog_loader.reload_cog(self.bot, name)
        if ok:
            await interaction.response.send_message(f"Reloaded {name}", ephemeral=True)
        else:
            await interaction.response.send_message(
                f"Failed to reload {name}: {err}", ephemeral=True,
            )

    @cogs.command(name="load", description="Load a cog")
    @owner_only()
    @app_commands.autocomplete(name=cog_name_autocomplete)
    async def cogs_load(self, interaction: discord.Interaction, name: str) -> None:
        """Load a cog."""
        ok, err = await cog_loader.load_cog(self.bot, name)
        if ok:
            await interaction.response.send_message(f"Loaded {name}", ephemeral=True)
        else:
            await interaction.response.send_message(
                f"Failed to load {name}: {err}", ephemeral=True,
            )
    @cogs.command(name="unload", description="Unload a cog")
    @owner_only()
    @app_commands.autocomplete(name=cog_name_autocomplete)
    async def cogs_unload(self, interaction: discord.Interaction, name: str) -> None:
        """Unload a cog."""
        ok, err = await cog_loader.unload_cog(self.bot, name)
        if ok:
            await interaction.response.send_message(
                f"Unloaded {name}", ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"Failed to unload {name}: {err}", ephemeral=True,
            )

    # ------------------------------------------------------------------
    @owner_only()
    @app_commands.command(name="logs", description="Show tail of log file")
    @app_commands.describe(lines="Number of lines to show")
    async def logs(self, interaction: discord.Interaction, lines: int = 200) -> None:
        """Send the last lines of the log file."""
        path = Path(settings.LOG_DIR) / "bot.log"
        try:
            content = await asyncio.to_thread(path.read_text, encoding="utf-8")
        except FileNotFoundError:
            await interaction.response.send_message(
                "Log file not found", ephemeral=True,
            )
            return
        data = "\n".join(content.splitlines()[-lines:])
        if len(data) > 1900:
            data = data[-1900:]
        await interaction.response.send_message(f"```\n{data}\n```", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    """Load the admin cog."""
    await bot.add_cog(Admin(bot))
