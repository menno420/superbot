from __future__ import annotations
import discord
from discord.ext import commands


async def post_log_embed(bot: commands.Bot, guild_id: int, embed: discord.Embed) -> None:
    """Post an embed to the guild's configured economy_log_channel (if set)."""
    from utils import db
    cid = await db.get_setting(guild_id, "economy_log_channel", "")
    if not cid:
        return
    ch = bot.get_channel(int(cid))
    if ch:
        try:
            await ch.send(embed=embed)
        except Exception:
            pass


def normalize_name(name: str) -> str:
    """Normalize a name to lowercase with no spaces for consistent role matching."""
    return name.lower().replace(" ", "")


class CogMenuView(discord.ui.View):
    """Reusable buttonized quick-reference menu for a cog's main commands."""

    def __init__(
        self,
        ctx: commands.Context,
        title: str,
        commands_info: list[tuple[str, str, str]],
    ):
        """
        commands_info: list of (command_name, usage, description) — max 25 entries.
        """
        super().__init__(timeout=120)
        self.ctx = ctx
        self.title = title
        self.commands_info = commands_info
        self.message: discord.Message | None = None

        for name, usage, desc in commands_info[:25]:
            self.add_item(_CmdButton(name, usage, desc))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True  # anyone can browse help menus

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=self.title,
            description="Click a button to see usage details for that command.",
            color=discord.Color.blurple(),
        )
        for name, _, desc in self.commands_info:
            embed.add_field(name=f"`!{name}`", value=desc, inline=True)
        return embed

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


class _CmdButton(discord.ui.Button):
    def __init__(self, name: str, usage: str, description: str):
        super().__init__(label=f"!{name}", style=discord.ButtonStyle.blurple)
        self._name = name
        self._usage = usage
        self._description = description

    async def callback(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title=f"!{self._name}",
            color=discord.Color.green(),
        )
        embed.add_field(name="Usage", value=f"`{self._usage}`", inline=False)
        embed.add_field(name="Description", value=self._description, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
