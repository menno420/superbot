"""Counting-game admin hub panel.

Top-level view shown by ``!countingmenu``.  Operates on the current
channel — toggles taking-turns, toggles reset-on-wrong, and resets
the count.  All mutations route through the cog's per-guild lock to
preserve the existing concurrency contract.
"""

from __future__ import annotations

import random
from datetime import datetime, timezone

import discord
from discord.ext import commands

from core.runtime import tasks
from views.base import HubView


class _CountingHubView(HubView):
    """Admin hub for managing the counting game in the current channel."""

    def __init__(self, ctx: commands.Context, cog):
        super().__init__(ctx.author)
        self.ctx = ctx
        self.cog = cog

    def _channel_data(self) -> dict | None:
        gid = str(self.ctx.guild.id)
        cid = str(self.ctx.channel.id)
        return self.cog.count_data.get(gid, {}).get("channels", {}).get(cid)

    async def build_embed(self) -> discord.Embed:
        embed = discord.Embed(title="🔢 Counting Manager", color=discord.Color.blue())
        ch_data = self._channel_data()
        if ch_data:
            mode = ch_data.get("mode", "normal").capitalize()
            current = ch_data.get("current_count", 0)
            turns = ch_data.get("taking_turns", False)
            reset_wrong = ch_data.get("reset_on_wrong_count", False)
            embed.description = f"Managing {self.ctx.channel.mention}"  # type: ignore[union-attr]
            embed.add_field(name="Mode", value=mode, inline=True)
            embed.add_field(name="Current Count", value=str(current), inline=True)
            embed.add_field(
                name="Taking Turns",
                value="✅" if turns else "❌",
                inline=True,
            )
            embed.add_field(
                name="Reset on Wrong",
                value="✅" if reset_wrong else "❌",
                inline=True,
            )
        else:
            gid = str(self.ctx.guild.id)
            active_ids = list(
                self.cog.count_data.get(gid, {}).get("channels", {}).keys(),
            )
            active_mentions = []
            for cid in active_ids:
                ch = self.ctx.guild.get_channel(int(cid))
                if ch:
                    active_mentions.append(ch.mention)
            embed.description = (
                f"{self.ctx.channel.mention} is not an active counting channel.\n\n"  # type: ignore[union-attr]
                "Start a new match with `!start_match <mode>`."
            )
            if active_mentions:
                embed.add_field(
                    name="Active Counting Channels",
                    value="\n".join(active_mentions),
                    inline=False,
                )
        embed.set_footer(text="Buttons below operate on the current channel.")
        return embed

    @discord.ui.button(
        label="🔄 Toggle Turns",
        style=discord.ButtonStyle.blurple,
        row=0,
    )
    async def btn_toggle_turns(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        gid = str(self.ctx.guild.id)
        cid = str(self.ctx.channel.id)
        async with self.cog.lock:
            ch_data = self.cog.count_data.get(gid, {}).get("channels", {}).get(cid)
            if not ch_data:
                await interaction.response.send_message(
                    "This channel is not an active counting channel.",
                    ephemeral=True,
                )
                return
            ch_data["taking_turns"] = not ch_data.get("taking_turns", False)
            tasks.spawn(f"counting:save:{gid}", self.cog._save_guild(gid))
        await interaction.response.edit_message(
            embed=await self.build_embed(),
            view=self,
        )

    @discord.ui.button(
        label="♻️ Toggle Reset",
        style=discord.ButtonStyle.blurple,
        row=0,
    )
    async def btn_toggle_reset(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        gid = str(self.ctx.guild.id)
        cid = str(self.ctx.channel.id)
        async with self.cog.lock:
            ch_data = self.cog.count_data.get(gid, {}).get("channels", {}).get(cid)
            if not ch_data:
                await interaction.response.send_message(
                    "This channel is not an active counting channel.",
                    ephemeral=True,
                )
                return
            ch_data["reset_on_wrong_count"] = not ch_data.get(
                "reset_on_wrong_count",
                False,
            )
            tasks.spawn(f"counting:save:{gid}", self.cog._save_guild(gid))
        await interaction.response.edit_message(
            embed=await self.build_embed(),
            view=self,
        )

    @discord.ui.button(label="🔁 Reset Count", style=discord.ButtonStyle.danger, row=0)
    async def btn_reset_count(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        gid = str(self.ctx.guild.id)
        cid = str(self.ctx.channel.id)
        async with self.cog.lock:
            ch_data = self.cog.count_data.get(gid, {}).get("channels", {}).get(cid)
            if not ch_data:
                await interaction.response.send_message(
                    "This channel is not an active counting channel.",
                    ephemeral=True,
                )
                return
            mode = ch_data.get("mode", "normal")
            start = 1000 if mode == "reverse" else 0
            ch_data["current_count"] = start
            ch_data["sequence_index"] = 0
            ch_data["last_user"] = None
            ch_data["leaderboard"] = {}
            ch_data["last_count_time"] = datetime.now(tz=timezone.utc).timestamp()
            if mode == "random":
                rand_range = ch_data.get("random_range", [1, 3])
                ch_data["next_expected"] = start + random.randint(*rand_range)
            tasks.spawn(f"counting:save:{gid}", self.cog._save_guild(gid))
        await interaction.response.edit_message(
            embed=await self.build_embed(),
            view=self,
        )

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary, row=1)
    async def btn_refresh(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.edit_message(
            embed=await self.build_embed(),
            view=self,
        )
