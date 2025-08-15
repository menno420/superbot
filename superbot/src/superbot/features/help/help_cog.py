"""Help command implementation."""

from __future__ import annotations

from collections import defaultdict

import discord
from discord import app_commands
from discord.ext import commands


class HelpCog(commands.Cog):
    """Provide slash and prefix help commands."""

    def __init__(self: HelpCog, bot: commands.Bot) -> None:
        """Store bot reference."""
        self.bot = bot

    def _build_index(self: HelpCog) -> discord.Embed:
        """Create an embed listing all commands."""
        commands_by_cog: dict[str, list[str]] = defaultdict(list)
        for cmd in self.bot.tree.walk_commands():
            if cmd.parent is None:
                commands_by_cog[cmd.cog_name or "slash"].append(f"/{cmd.name}")
        for cmd in self.bot.commands:
            if not cmd.hidden:
                commands_by_cog[cmd.cog_name or "prefix"].append(
                    f"{self.bot.command_prefix}{cmd.name}",
                )
        embed = discord.Embed(title="Commands")
        for cog_name, names in sorted(commands_by_cog.items()):
            embed.add_field(
                name=cog_name,
                value=", ".join(sorted(names)) or "-",
                inline=False,
            )
        return embed

    def _command_details(self: HelpCog, name: str) -> discord.Embed:
        """Build detailed help for a single command."""
        for cmd in self.bot.tree.walk_commands():
            if cmd.name == name:
                return discord.Embed(title=f"/{cmd.name}", description=cmd.description)
        for cmd in self.bot.commands:
            if cmd.name == name:
                return discord.Embed(
                    title=f"{self.bot.command_prefix}{cmd.name}",
                    description=cmd.help or "",
                )
        return discord.Embed(title="Unknown command")

    @app_commands.command(name="help", description="Show bot commands")
    @app_commands.describe(command="Command to describe")
    async def slash_help(
        self: HelpCog,
        interaction: discord.Interaction,
        command: str | None = None,
    ) -> None:
        """Respond to the /help command."""
        embed = self._command_details(command) if command else self._build_index()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.command(name="help")
    async def prefix_help(
        self: HelpCog,
        ctx: commands.Context[commands.Bot],
        *,
        command: str | None = None,
    ) -> None:
        """Handle the !help command."""
        embed = self._command_details(command) if command else self._build_index()
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Add the cog to the bot."""
    await bot.add_cog(HelpCog(bot))
