"""PvP play-and-resolve view.

Sent to the channel once both players accept.  Each player clicks
"Pick your move" → gets an ephemeral :class:`_RpsMovePickerView` →
their choice is recorded back here.  When both picks land, the result
is computed and payouts flow through :mod:`services.economy_service`.
"""

from __future__ import annotations

import discord

from services import economy_service
from utils.ui_constants import GAME_COLOR, SUCCESS_COLOR
from views.rps._helpers import _FREE_WIN


class _RpsPvpPlayView(discord.ui.View):
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
        if len(self.choices) == 2:
            await self._resolve()

    async def _resolve(self):
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        try:
            await self.message.edit(view=self)
        except Exception:
            pass
        self.stop()

        m1 = self.choices.get(self.p1.id, "forfeit")
        m2 = self.choices.get(self.p2.id, "forfeit")

        def _wins(a, b):
            return {"rock": "scissors", "scissors": "paper", "paper": "rock"}.get(
                a,
            ) == b

        e = {"rock": "🪨", "paper": "📄", "scissors": "✂️", "forfeit": "❌"}

        if m1 == "forfeit" and m2 == "forfeit":
            result, coin_delta, winner_id = "🤝 Both forfeited.", 0, None
        elif m1 == "forfeit":
            result, coin_delta, winner_id = (
                f"{self.p2.mention} wins (opponent forfeited)!",
                self.bet,
                self.p2.id,
            )
        elif m2 == "forfeit":
            result, coin_delta, winner_id = (
                f"{self.p1.mention} wins (opponent forfeited)!",
                self.bet,
                self.p1.id,
            )
        elif m1 == m2:
            result, coin_delta, winner_id = "🤝 Tie! No coins exchanged.", 0, None
        elif _wins(m1, m2):
            result, coin_delta, winner_id = (
                f"🎉 {self.p1.mention} wins!",
                self.bet,
                self.p1.id,
            )
        else:
            result, coin_delta, winner_id = (
                f"🎉 {self.p2.mention} wins!",
                self.bet,
                self.p2.id,
            )

        if coin_delta and winner_id:
            loser_id = self.p2.id if winner_id == self.p1.id else self.p1.id
            payout = coin_delta if coin_delta else _FREE_WIN
            # Preserves prior semantics: winner always credited the full
            # payout; loser debited down to floor-zero if short (overdraft
            # allowed). Using economy_service.transfer would atomically
            # reject the move on insufficient loser balance — that is the
            # safer pattern but a behaviour change; revisit when game
            # rules formalise bet escrow.
            await economy_service.credit(
                self.guild_id,
                winner_id,
                payout,
                reason="rps:pvp_win",
            )
            await economy_service.debit(
                self.guild_id,
                loser_id,
                payout,
                reason="rps:pvp_loss",
                allow_overdraft=True,
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
        await self.channel.send(embed=embed)

    async def on_timeout(self):
        # Anyone who didn't choose forfeits
        for pid in (self.p1.id, self.p2.id):
            if pid not in self.choices:
                self.choices[pid] = "forfeit"
        if len(self.choices) == 2:
            await self._resolve()
