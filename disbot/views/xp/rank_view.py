"""Rank navigation view (S4.2-followup extraction).

``_RankView`` is the ephemeral wrapper around ``!rank`` output that
lets the invoking user flip between "Both / XP / Coins" stat views
via the ``_RankSelect`` dropdown.  Timeout removes the dropdown.
"""

from __future__ import annotations

import discord

from cogs.xp._helpers import _build_rank_embed


class _RankView(discord.ui.View):
    """Navigation dropdown for the rank card — lets users switch stat views."""

    def __init__(
        self,
        member: discord.Member,
        guild: discord.Guild,
        current_stat: str,
    ):
        super().__init__(timeout=120)
        self.member = member
        self.guild = guild
        self.message: discord.Message | None = None
        self.add_item(_RankSelect(self, current_stat))

    async def on_timeout(self) -> None:
        if self.message:
            try:
                await self.message.edit(view=None)
            except Exception:
                pass


class _RankSelect(discord.ui.Select):
    def __init__(self, rank_view: _RankView, current_stat: str):
        options = [
            discord.SelectOption(
                label="Both (XP & Coins)",
                value="both",
                emoji="📊",
                default=(current_stat == "both"),
            ),
            discord.SelectOption(
                label="XP",
                value="xp",
                emoji="🏆",
                default=(current_stat == "xp"),
            ),
            discord.SelectOption(
                label="Coins",
                value="coins",
                emoji="🪙",
                default=(current_stat == "coins"),
            ),
        ]
        super().__init__(
            placeholder="Switch stat view…",
            options=options,
            min_values=1,
            max_values=1,
        )
        self._rank_view = rank_view

    async def callback(self, interaction: discord.Interaction) -> None:
        stat = self.values[0]
        for opt in self.options:
            opt.default = opt.value == stat
        embed = await _build_rank_embed(
            self._rank_view.member,
            self._rank_view.guild,
            stat,
        )
        await interaction.response.edit_message(embed=embed, view=self.view)
