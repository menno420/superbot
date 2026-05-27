"""PvP challenge accept/decline view.

Spawned from ``!rpspvp <opponent>``.  The opponent (only the opponent
can interact) either accepts — which transitions to a
:class:`_RpsPvpPlayView` for both players to pick moves — or declines.
"""

from __future__ import annotations

import logging

import discord

from core.runtime.interaction_helpers import safe_edit
from services import game_state_service
from views.rps._helpers import (
    RPS_PVP_PENDING_SUBSYSTEM,
    RPS_PVP_PENDING_VERSION,
    _rps_pvp_pending,
    rps_pvp_canonical_user_id,
)

logger = logging.getLogger("bot.rps.pvp_challenge")


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
        # Bail if the edit fails: the rest of this handler persists the
        # pending match and spawns the play view in the channel, and
        # an already-failed interaction means the players won't see the
        # accepted state.
        if not await safe_edit(
            interaction,
            content="✅ Challenge accepted — both players, choose your move!",
            view=self,
        ):
            return
        key = frozenset({self.challenger.id, self.opponent.id})
        _rps_pvp_pending[key] = {
            "choices": {},
            "guild_id": self.guild_id,
            "bet": self.bet,
            "channel_id": interaction.channel_id,
        }
        # PR G1 — persist the pending match so cog_load can drop
        # stranded rows after a restart.  The view itself cannot be
        # restored (live view objects do not survive a process bounce),
        # so the saved state is recovery telemetry, not a resume
        # surface: cog_load lists and clears.  Failures are non-fatal —
        # the in-memory dict above is the authoritative source while
        # the bot is alive.
        try:
            await game_state_service.save(
                guild_id=self.guild_id,
                user_id=rps_pvp_canonical_user_id(
                    self.challenger.id,
                    self.opponent.id,
                ),
                channel_id=interaction.channel_id,
                subsystem=RPS_PVP_PENDING_SUBSYSTEM,
                state={
                    "p1_id": self.challenger.id,
                    "p2_id": self.opponent.id,
                    "guild_id": self.guild_id,
                    "channel_id": interaction.channel_id,
                    "bet": self.bet,
                    "choices": {},
                },
                version=RPS_PVP_PENDING_VERSION,
            )
        except Exception as exc:
            logger.warning("rps_pvp_pending save (accept) failed: %s", exc)
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
        await safe_edit(
            interaction,
            content=f"❌ {self.opponent.display_name} declined the challenge.",
            view=self,
        )
        self.stop()

    async def on_timeout(self):
        if self.message is None:
            self.stop()
            return
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        try:
            await self.message.edit(content="⏰ Challenge timed out.", view=self)
        except Exception:
            pass
        self.stop()
