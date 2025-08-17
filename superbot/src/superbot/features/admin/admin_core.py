"""Admin slash commands."""

from __future__ import annotations

import logging
from time import perf_counter
from typing import cast

import discord
from discord import app_commands
from discord.ext import commands

from superbot.config import Settings
from superbot.loaders import cogs as cog_loader


def _is_owner(interaction: discord.Interaction) -> bool:
    """Return True if the interaction author is in OWNER_IDS."""
    bot = cast(commands.Bot, interaction.client)
    settings: Settings = bot.settings
    return interaction.user and interaction.user.id in settings.owner_ids


def owner_only() -> app_commands.Check:
    """Decorator to restrict slash commands to owners."""
    return app_commands.check(_is_owner)


def _is_owner_ctx(ctx: commands.Context[commands.Bot]) -> bool:
    """Return True if ctx.author is an owner."""
    settings: Settings = ctx.bot.settings
    return ctx.author.id in settings.owner_ids


def owner_only_command() -> commands.Check:
    """Decorator to restrict prefix commands to owners."""
    return commands.check(_is_owner_ctx)


class AdminCog(commands.Cog):
    """Administrative commands for bot owners."""

    def __init__(self: AdminCog, bot: commands.Bot) -> None:
        """Store bot reference and logger."""
        self.bot = bot
        self.log = logging.getLogger("superbot")

    admin = app_commands.Group(name="admin", description="Admin commands")

    @admin.command(name="sync")
    @owner_only()
    @app_commands.describe(scope="guild or global")
    async def sync(
        self: AdminCog,
        interaction: discord.Interaction,
        scope: str = "guild",
    ) -> None:
        """Synchronize slash commands."""
        start = perf_counter()
        results: list[str] = []
        if self.bot.settings.guild_ids and scope == "guild":
            for gid in self.bot.settings.guild_ids:
                cmds = await self.bot.tree.sync(guild=discord.Object(id=gid))
                results.append(f"{gid}: {len(cmds)}")
        else:
            cmds = await self.bot.tree.sync()
            results.append(f"global: {len(cmds)}")
        duration = perf_counter() - start
        embed = discord.Embed(title="Sync", description="\n".join(results))
        embed.set_footer(text=f"{duration:.2f}s")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @admin.command(name="cogs")
    @owner_only()
    async def list_cogs(self: AdminCog, interaction: discord.Interaction) -> None:
        """List loaded extensions."""
        names = cog_loader.list_loaded(self.bot)
        embed = discord.Embed(
            title="Loaded cogs",
            description="\n".join(names) or "none",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @admin.command(name="load")
    @owner_only()
    @app_commands.describe(name="Extension to load")
    async def load(
        self: AdminCog,
        interaction: discord.Interaction,
        name: str,
    ) -> None:
        """Load an extension."""
        await cog_loader.load_one(self.bot, name)
        await interaction.response.send_message(f"loaded {name}", ephemeral=True)

    @admin.command(name="unload")
    @owner_only()
    @app_commands.describe(name="Extension to unload")
    async def unload(
        self: AdminCog,
        interaction: discord.Interaction,
        name: str,
    ) -> None:
        """Unload an extension."""
        await cog_loader.unload_one(self.bot, name)
        await interaction.response.send_message(f"unloaded {name}", ephemeral=True)

    @admin.command(name="reload")
    @owner_only()
    @app_commands.describe(name="Extension to reload")
    async def reload(
        self: AdminCog,
        interaction: discord.Interaction,
        name: str,
    ) -> None:
        """Reload an extension."""
        await cog_loader.reload_one(self.bot, name)
        await interaction.response.send_message(f"reloaded {name}", ephemeral=True)

    @admin.command(name="restart")
    @owner_only()
    async def restart(self: AdminCog, interaction: discord.Interaction) -> None:
        """Restart the bot process."""
        await interaction.response.send_message("Restarting...", ephemeral=True)
        self.log.info("restart requested")
        await self.bot.close()

    @commands.group(name="cog", invoke_without_command=True)
    @owner_only_command()
    async def cog_group(self: AdminCog, ctx: commands.Context[commands.Bot]) -> None:
        """Base command for cog management."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Usage: !cog [load|unload|reload] <name>")

    @cog_group.command(name="load")
    @owner_only_command()
    async def cog_load(
        self: AdminCog,
        ctx: commands.Context[commands.Bot],
        name: str,
    ) -> None:
        """Load an extension via prefix command."""
        await cog_loader.load_one(self.bot, name)
        await ctx.send(f"loaded {name}")

    @cog_group.command(name="unload")
    @owner_only_command()
    async def cog_unload(
        self: AdminCog,
        ctx: commands.Context[commands.Bot],
        name: str,
    ) -> None:
        """Unload an extension via prefix command."""
        await cog_loader.unload_one(self.bot, name)
        await ctx.send(f"unloaded {name}")

    @cog_group.command(name="reload")
    @owner_only_command()
    async def cog_reload(
        self: AdminCog,
        ctx: commands.Context[commands.Bot],
        name: str,
    ) -> None:
        """Reload an extension via prefix command."""
        await cog_loader.reload_one(self.bot, name)
        await ctx.send(f"reloaded {name}")


async def setup(bot: commands.Bot) -> None:
    """Add the cog to the bot."""
    await bot.add_cog(AdminCog(bot))
