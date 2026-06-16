"""Counting-game admin hub panel.

Shown by ``!countingmenu`` / ``!cm``.  Pick any text channel with the
selector, then manage *that* channel: toggle taking-turns, toggle
reset-on-wrong, reset the count, enable counting on an existing channel
(the "whitelist" flow a tester asked for), or disable it again without
deleting the channel.  All mutations route through the cog, which owns
the per-guild lock + persistence, preserving the concurrency contract.
"""

from __future__ import annotations

import discord
from discord.ext import commands

from core.runtime import resources
from views.base import HubView

# No-argument modes enable-able straight from the panel.  ``multiples``
# (needs a factor) and ``custom`` (needs a sequence) keep the
# argument-taking ``!start_match`` path.
_ENABLE_MODES = (
    "normal",
    "reverse",
    "skip",
    "random",
    "prime",
    "fibonacci",
    "squares",
    "cubes",
    "factorials",
)


class _ChannelPick(discord.ui.ChannelSelect):
    """Pick which channel the panel manages (any text channel)."""

    def __init__(self, hub: _CountingHubView) -> None:
        super().__init__(
            placeholder="Select a channel to manage…",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=0,
        )
        self._hub = hub

    async def callback(self, interaction: discord.Interaction) -> None:
        self._hub.selected_cid = str(self.values[0].id)
        await self._hub.rerender(interaction)


class _ModePick(discord.ui.Select):
    """Enable counting on the selected (currently inactive) channel."""

    def __init__(self, hub: _CountingHubView) -> None:
        super().__init__(
            placeholder="Enable counting here — pick a mode…",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label=mode.capitalize(), value=mode)
                for mode in _ENABLE_MODES
            ],
            row=1,
        )
        self._hub = hub

    async def callback(self, interaction: discord.Interaction) -> None:
        await self._hub.cog.enable_channel(
            self._hub.gid,
            self._hub.selected_cid,
            self.values[0],
        )
        await self._hub.rerender(interaction)


class _ToggleTurnsButton(discord.ui.Button):
    def __init__(self, hub: _CountingHubView) -> None:
        super().__init__(
            label="🔄 Toggle Turns",
            style=discord.ButtonStyle.blurple,
            row=2,
        )
        self._hub = hub

    async def callback(self, interaction: discord.Interaction) -> None:
        await self._hub.cog.toggle_channel_flag(
            self._hub.gid,
            self._hub.selected_cid,
            "taking_turns",
        )
        await self._hub.rerender(interaction)


class _ToggleResetButton(discord.ui.Button):
    def __init__(self, hub: _CountingHubView) -> None:
        super().__init__(
            label="♻️ Toggle Reset",
            style=discord.ButtonStyle.blurple,
            row=2,
        )
        self._hub = hub

    async def callback(self, interaction: discord.Interaction) -> None:
        await self._hub.cog.toggle_channel_flag(
            self._hub.gid,
            self._hub.selected_cid,
            "reset_on_wrong_count",
        )
        await self._hub.rerender(interaction)


class _ResetCountButton(discord.ui.Button):
    def __init__(self, hub: _CountingHubView) -> None:
        super().__init__(
            label="🔁 Reset Count",
            style=discord.ButtonStyle.danger,
            row=2,
        )
        self._hub = hub

    async def callback(self, interaction: discord.Interaction) -> None:
        await self._hub.cog.reset_channel_count(
            self._hub.gid,
            self._hub.selected_cid,
        )
        await self._hub.rerender(interaction)


class _DisableButton(discord.ui.Button):
    def __init__(self, hub: _CountingHubView) -> None:
        super().__init__(
            label="🛑 Disable Here",
            style=discord.ButtonStyle.danger,
            row=3,
        )
        self._hub = hub

    async def callback(self, interaction: discord.Interaction) -> None:
        disabled = await self._hub.cog.disable_channel(
            self._hub.gid,
            self._hub.selected_cid,
        )
        # Send a confirmation message — counting is off in that channel now.
        # The panel user can select another channel or use !start_match.
        msg = (
            "Counting disabled in that channel."
            if disabled
            else "That channel wasn't an active counting channel."
        )
        await interaction.response.send_message(msg, ephemeral=True)


class _RefreshButton(discord.ui.Button):
    def __init__(self, hub: _CountingHubView) -> None:
        super().__init__(
            label="🔄 Refresh",
            style=discord.ButtonStyle.secondary,
            row=3,
        )
        self._hub = hub

    async def callback(self, interaction: discord.Interaction) -> None:
        await self._hub.rerender(interaction)


class _CountingHubView(HubView):
    """Admin hub for selecting + managing counting channels."""

    def __init__(self, ctx: commands.Context, cog) -> None:
        super().__init__(ctx.author)
        self.ctx = ctx
        self.cog = cog
        self.gid = str(ctx.guild.id)
        self.selected_cid = str(ctx.channel.id)
        self._rebuild()

    # -- state ---------------------------------------------------------
    def _channel_data(self) -> dict | None:
        return (
            self.cog.count_data.get(self.gid, {})
            .get("channels", {})
            .get(self.selected_cid)
        )

    def _selected_mention(self) -> str:
        ch = resources.resolve_channel(
            self.ctx.guild,
            channel_id=self.selected_cid,
        )
        return ch.mention if ch else f"`{self.selected_cid}`"

    def _active_mentions(self) -> list[str]:
        mentions: list[str] = []
        channels = self.cog.count_data.get(self.gid, {}).get("channels", {})
        for cid in channels:
            ch = resources.resolve_channel(self.ctx.guild, channel_id=cid)
            if ch:
                mentions.append(ch.mention)
        return mentions

    # -- component assembly --------------------------------------------
    def _rebuild(self) -> None:
        for child in list(self.children):
            self.remove_item(child)
        self.add_item(_ChannelPick(self))
        if self._channel_data() is None:
            self.add_item(_ModePick(self))
        else:
            self.add_item(_ToggleTurnsButton(self))
            self.add_item(_ToggleResetButton(self))
            self.add_item(_ResetCountButton(self))
            self.add_item(_DisableButton(self))
        self.add_item(_RefreshButton(self))

    async def rerender(self, interaction: discord.Interaction) -> None:
        self._rebuild()
        await interaction.response.edit_message(
            embed=await self.build_embed(),
            view=self,
        )

    # -- embed ---------------------------------------------------------
    async def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🔢 Counting Manager",
            color=discord.Color.blue(),
        )
        ch_data = self._channel_data()
        if ch_data:
            embed.description = f"Managing {self._selected_mention()}"
            embed.add_field(
                name="Mode",
                value=ch_data.get("mode", "normal").capitalize(),
                inline=True,
            )
            embed.add_field(
                name="Current Count",
                value=str(ch_data.get("current_count", 0)),
                inline=True,
            )
            embed.add_field(
                name="Taking Turns",
                value="✅" if ch_data.get("taking_turns", False) else "❌",
                inline=True,
            )
            embed.add_field(
                name="Reset on Wrong",
                value="✅" if ch_data.get("reset_on_wrong_count", False) else "❌",
                inline=True,
            )
            embed.set_footer(text="Buttons operate on the selected channel.")
        else:
            embed.description = (
                f"{self._selected_mention()} is not an active counting "
                "channel.\n\nPick a mode below to **enable counting here**, or "
                "select another channel above. `!start_match <mode>` still "
                "creates a fresh channel."
            )
            active = self._active_mentions()
            if active:
                embed.add_field(
                    name="Active Counting Channels",
                    value="\n".join(active),
                    inline=False,
                )
            embed.set_footer(text="Select a channel above to manage it.")
        return embed
