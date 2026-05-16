"""PvP challenge accept/decline view.

Spawned from ``!rpspvp <opponent>``.  The opponent (only the opponent
can interact) either accepts — which transitions to a
:class:`_RpsPvpPlayView` for both players to pick moves — or declines.
"""

from __future__ import annotations

import discord

from views.rps._helpers import _rps_pvp_pending


class _RpsPvpChallengeView(discord.ui.View):
    def __init__(
        self,
        challenger: discord.Member,
        opponent: discord.Member,
        guild_id: int,
        bet: int,
    ):
        super().__init__(timeout=60)
        self.challenger = challenger
        self.opponent = opponent
        self.guild_id = guild_id
        self.bet = bet
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message(
                "This challenge isn't for you.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, emoji="✅")
    async def accept(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Local import avoids the views.rps.pvp_play → views.rps.pvp_challenge
        # cycle.
        from views.rps.pvp_play import _RpsPvpPlayView

        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        await interaction.response.edit_message(
            content="✅ Challenge accepted — both players, choose your move!",
            view=self,
        )
        key = frozenset({self.challenger.id, self.opponent.id})
        _rps_pvp_pending[key] = {
            "choices": {},
            "guild_id": self.guild_id,
            "bet": self.bet,
            "channel_id": interaction.channel_id,
        }
        ch = interaction.channel
        play_view = _RpsPvpPlayView(
            self.challenger,
            self.opponent,
            self.guild_id,
            self.bet,
            ch,  # type: ignore[arg-type]
        )
        await ch.send(  # type: ignore[union-attr]
            f"{self.challenger.mention} {self.opponent.mention} — click below to "
            "pick your move (only you can see your choice):",
            view=play_view,
        )
        self.stop()

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red, emoji="❌")
    async def decline(self, interaction: discord.Interaction, _: discord.ui.Button):
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        await interaction.response.edit_message(
            content=f"❌ {self.opponent.display_name} declined the challenge.",
            view=self,
        )
        self.stop()

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        try:
            await self.message.edit(content="⏰ Challenge timed out.", view=self)
        except Exception:
            pass
