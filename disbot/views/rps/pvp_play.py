"""PvP play-and-resolve view.

Sent to the channel once both players accept.  Each player clicks
"Pick your move" → gets an ephemeral :class:`_RpsMovePickerView` →
their choice is recorded back here.  When both picks land, the result
is computed and the escrowed pot is settled through
:mod:`services.game_wager_workflow` (P0-1 — stakes were escrowed at
challenge-accept time, so settle is atomic + idempotent).
"""

from __future__ import annotations

import logging

import discord

from services import game_state_service, game_wager_workflow
from utils.terminal_guard import SettleOnceMixin
from utils.ui_constants import GAME_COLOR, SUCCESS_COLOR
from views.rps._helpers import (
    RPS_PVP_ESCROW_SUBSYSTEM,
    RPS_PVP_PENDING_SUBSYSTEM,
    RPS_PVP_PENDING_VERSION,
    rps_pvp_canonical_user_id,
)

logger = logging.getLogger("bot.rps.pvp_play")


class _RpsPvpResultView(discord.ui.View):
    """Terminal screen after a PvP match resolves — never a dead-end.

    The PvP result used to be posted as a bare channel embed with no
    controls (completion cert punch-list #2), stranding both players. This
    view carries the shared **◀ Back to RPS** affordance every other RPS
    sub-view already uses (`_make_rps_back_button`), so either player is one
    click from the RPS hub. Either match participant may use it; the back
    panel opens for whoever clicks (its author is read off the interaction).
    """

    def __init__(self, p1: discord.Member, p2: discord.Member) -> None:
        super().__init__(timeout=180)
        self.p1 = p1
        self.p2 = p2
        self.message: discord.Message | None = None
        # Late import: rps_panel imports this module's siblings, so a
        # module-level import would create a cycle (mirrors solo_play).
        from views.games.rps_panel import _make_rps_back_button

        self.add_item(_make_rps_back_button())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in (self.p1.id, self.p2.id):
            await interaction.response.send_message(
                "You're not part of this match.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        if self.message is None:
            return
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        try:
            await self.message.edit(view=self)
        except Exception as exc:
            logger.debug("rps_pvp result on_timeout: message.edit failed: %s", exc)


class _RpsPvpPlayView(SettleOnceMixin, discord.ui.View):
    """Visible to the channel; each player clicks for their ephemeral picker."""

    def __init__(
        self,
        p1: discord.Member,
        p2: discord.Member,
        guild_id: int,
        bet: int,
        channel: discord.TextChannel,
    ):
        super().__init__(timeout=60)
        self.p1 = p1
        self.p2 = p2
        self.guild_id = guild_id
        self.bet = bet
        self.channel = channel
        self.choices: dict[int, str] = {}
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in (self.p1.id, self.p2.id):
            await interaction.response.send_message(
                "You're not part of this match.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(
        label="Pick your move",
        style=discord.ButtonStyle.blurple,
        emoji="✂️",
    )
    async def pick(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Local import — move_picker references this view via parent.
        from views.rps.move_picker import _RpsMovePickerView

        if interaction.user.id in self.choices:
            await interaction.response.send_message(
                "You already picked!",
                ephemeral=True,
            )
            return
        picker_view = _RpsMovePickerView(interaction.user.id, self)
        await interaction.response.send_message(
            "Choose your move — only you can see this:",
            view=picker_view,
            ephemeral=True,
        )

    async def record_choice(self, user_id: int, move: str):
        self.choices[user_id] = move
        # PR G1 — persist the partial-choice state so cog_load can find
        # stranded matches after a crash.  Best-effort: failures here
        # never block gameplay (in-memory dict above is authoritative).
        try:
            await game_state_service.save(
                guild_id=self.guild_id,
                user_id=rps_pvp_canonical_user_id(self.p1.id, self.p2.id),
                channel_id=self.channel.id,
                subsystem=RPS_PVP_PENDING_SUBSYSTEM,
                state={
                    "p1_id": self.p1.id,
                    "p2_id": self.p2.id,
                    "guild_id": self.guild_id,
                    "channel_id": self.channel.id,
                    "bet": self.bet,
                    # JSON-safe: stringify int keys.
                    "choices": {str(uid): m for uid, m in self.choices.items()},
                },
                version=RPS_PVP_PENDING_VERSION,
            )
        except Exception as exc:
            logger.warning("rps_pvp_pending save (record_choice) failed: %s", exc)
        if len(self.choices) == 2:
            await self._resolve()

    async def _resolve(self):
        # Settle-once: ``_resolve`` is reachable twice — both players' picks
        # landing near-simultaneously (the second ``record_choice`` re-sees
        # ``len == 2`` while the first is still awaiting), or ``on_timeout``
        # racing a final pick. A second settlement would post a duplicate result
        # embed and re-call the (idempotent) wager settle. Claim synchronously
        # before any await so the loser short-circuits.
        if not self.claim_settlement():
            return
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        try:
            await self.message.edit(view=self)
        except Exception as exc:
            logger.debug("rps_pvp _resolve: disable-buttons edit failed: %s", exc)
        self.stop()

        m1 = self.choices.get(self.p1.id, "forfeit")
        m2 = self.choices.get(self.p2.id, "forfeit")

        def _wins(a, b):
            return {"rock": "scissors", "scissors": "paper", "paper": "rock"}.get(
                a,
            ) == b

        e = {"rock": "🪨", "paper": "📄", "scissors": "✂️", "forfeit": "❌"}

        if m1 == "forfeit" and m2 == "forfeit":
            result, _, winner_id = "🤝 Both forfeited.", 0, None
        elif m1 == "forfeit":
            result, _, winner_id = (
                f"{self.p2.mention} wins (opponent forfeited)!",
                self.bet,
                self.p2.id,
            )
        elif m2 == "forfeit":
            result, _, winner_id = (
                f"{self.p1.mention} wins (opponent forfeited)!",
                self.bet,
                self.p1.id,
            )
        elif m1 == m2:
            result, _, winner_id = "🤝 Tie! No coins exchanged.", 0, None
        elif _wins(m1, m2):
            result, _, winner_id = (
                f"🎉 {self.p1.mention} wins!",
                self.bet,
                self.p1.id,
            )
        else:
            result, _, winner_id = (
                f"🎉 {self.p2.mention} wins!",
                self.bet,
                self.p2.id,
            )

        # P0-1 (D1) — the stakes were escrowed at accept.  Pay the pot to
        # the winner, or return both stakes on a tie / double-forfeit.
        # Both legs are atomic + idempotent inside the wager workflow, so
        # no crash here can mint coins or leave the pot stranded.
        if self.bet > 0:
            kwargs = {
                "guild_id": self.guild_id,
                "channel_id": self.channel.id,
                "subsystem": RPS_PVP_ESCROW_SUBSYSTEM,
                "p1_id": self.p1.id,
                "p2_id": self.p2.id,
            }
            if winner_id:
                await game_wager_workflow.settle_pvp(
                    **kwargs,
                    winner_id=winner_id,
                    reason="rps:pvp_win",
                )
            else:
                await game_wager_workflow.refund_pvp(
                    **kwargs,
                    reason="rps:pvp_refund",
                )

        embed = discord.Embed(
            title="✂️ RPS PvP Result",
            description=(
                f"{self.p1.mention}: **{m1}** {e.get(m1, '')}\n"
                f"{self.p2.mention}: **{m2}** {e.get(m2, '')}\n\n"
                f"{result}"
            ),
            color=SUCCESS_COLOR if winner_id else GAME_COLOR,
        )
        # Not a dead-end (cert punch-list #2): post the result with a
        # ◀ Back to RPS affordance so neither player is stranded on a bare
        # channel embed.
        result_view = _RpsPvpResultView(self.p1, self.p2)
        result_view.message = await self.channel.send(embed=embed, view=result_view)

        # PR G1 — match resolved naturally; drop the persisted state.
        try:
            await game_state_service.clear(
                guild_id=self.guild_id,
                user_id=rps_pvp_canonical_user_id(self.p1.id, self.p2.id),
                channel_id=self.channel.id,
                subsystem=RPS_PVP_PENDING_SUBSYSTEM,
            )
        except Exception as exc:
            logger.warning("rps_pvp_pending clear failed: %s", exc)

    async def on_timeout(self):
        # Anyone who didn't choose forfeits
        for pid in (self.p1.id, self.p2.id):
            if pid not in self.choices:
                self.choices[pid] = "forfeit"
        if len(self.choices) == 2:
            await self._resolve()
