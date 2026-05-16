from __future__ import annotations

import re

import discord
from discord.ext import commands

from utils.settings_keys import ECONOMY_LOG_CHANNEL
from utils.ui_constants import INFO_COLOR, SUCCESS_COLOR


def _parse_member(guild: discord.Guild, text: str) -> discord.Member | None:
    """Resolve a member from a mention, ID, or username/display-name string."""
    text = text.strip()
    mention_match = re.match(r"<@!?(\d+)>", text)
    if mention_match:
        return guild.get_member(int(mention_match.group(1)))
    if text.isdigit():
        return guild.get_member(int(text))
    return discord.utils.find(
        lambda m: m.name == text or m.display_name == text,
        guild.members,
    )


_CUSTOM_EMOJI_RE = re.compile(r"<a?:(\w+):(\d+)>")


def safe_select_emoji(
    value: str | discord.PartialEmoji | None,
) -> str | discord.PartialEmoji | None:
    """Return a valid SelectOption emoji or None if the value cannot be used.

    Handles unicode emoji strings, <:name:id> custom emoji, and PartialEmoji
    objects. Rejects plain ASCII characters that Discord rejects.
    """
    if value is None:
        return None
    if isinstance(value, discord.PartialEmoji):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    stripped = value.strip()
    m = _CUSTOM_EMOJI_RE.match(stripped)
    if m:
        animated = stripped.startswith("<a:")
        return discord.PartialEmoji(
            name=m.group(1),
            id=int(m.group(2)),
            animated=animated,
        )
    # Reject single plain ASCII characters (e.g. "#") — not valid Discord emoji
    if len(stripped) == 1 and ord(stripped) < 128:
        return None
    return stripped


async def post_log_embed(
    bot: commands.Bot,
    guild_id: int,
    embed: discord.Embed,
) -> None:
    """Post an embed to the guild's configured economy_log_channel (if set)."""
    from utils import db

    cid = await db.get_setting(guild_id, ECONOMY_LOG_CHANNEL, "")
    if not cid:
        return
    ch = bot.get_channel(int(cid))
    if ch:
        try:
            await ch.send(embed=embed)  # type: ignore[union-attr]
        except Exception:
            pass


def normalize_name(name: str) -> str:
    """Normalize a name to lowercase with no spaces or underscores for consistent role matching."""
    return name.lower().replace(" ", "").replace("_", "")


class CogMenuView(discord.ui.View):
    """Reusable command-reference menu using a Select dropdown with in-place updates.

    commands_info: list of (command_name, usage, description) — max 25 entries.
    """

    def __init__(
        self,
        ctx: commands.Context,
        title: str,
        commands_info: list[tuple[str, str, str]],
    ):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.title = title
        self.commands_info = commands_info[:25]
        self.message: discord.Message | None = None

        options = [
            discord.SelectOption(label=f"!{name}", description=desc[:100], value=str(i))
            for i, (name, _, desc) in enumerate(self.commands_info)
        ]
        self._select = _CommandSelect(options, self)
        self.add_item(self._select)
        self.add_item(_OverviewButton(self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=self.title,
            description="Select a command below to see its full usage details.",
            color=INFO_COLOR,
        )
        for name, _usage, desc in self.commands_info:
            embed.add_field(name=f"`!{name}`", value=desc[:120], inline=True)
        return embed

    def build_command_embed(self, idx: int) -> discord.Embed:
        name, usage, desc = self.commands_info[idx]
        embed = discord.Embed(title=f"`!{name}`", color=SUCCESS_COLOR)
        embed.add_field(name="Usage", value=f"`{usage}`", inline=False)
        embed.add_field(name="Description", value=desc, inline=False)
        embed.set_footer(
            text=f"{self.title} • Select another command or click Overview",
        )
        return embed

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


class _CommandSelect(discord.ui.Select):
    def __init__(self, options: list[discord.SelectOption], menu: CogMenuView):
        super().__init__(
            placeholder="Select a command…",
            options=options,
            min_values=1,
            max_values=1,
        )
        self.menu = menu

    async def callback(self, interaction: discord.Interaction) -> None:
        idx = int(self.values[0])
        embed = self.menu.build_command_embed(idx)
        await interaction.response.edit_message(embed=embed, view=self.view)


class _OverviewButton(discord.ui.Button):
    def __init__(self, menu: CogMenuView):
        super().__init__(label="Overview", style=discord.ButtonStyle.secondary, row=1)
        self.menu = menu

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(
            embed=self.menu.build_embed(),
            view=self.view,
        )
