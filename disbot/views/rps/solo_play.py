"""Single-player Rock·Paper·Scissors view.

Three buttons → pick a move → resolve against a random bot pick →
apply the coin delta via :mod:`services.economy_service`.

The bet is not pre-escrowed (the user can play with zero balance and
lose nothing more than they already have).  Win credits, loss debits
with overdraft allowed to preserve the original floor-at-zero
behaviour.
"""

from __future__ import annotations

import random

import discord

from services import economy_service
from utils import db as global_db
from utils.ui_constants import ERROR_COLOR, GAME_COLOR, SUCCESS_COLOR
from views.rps._helpers import _FREE_WIN, _RPS_EMOJI, _RPS_WINS


class _RpsView(discord.ui.View):
    def __init__(self, user: discord.Member, guild_id: int, bet: int):
        super().__init__(timeout=60)
        self.user = user
        self.guild_id = guild_id
        self.bet = bet
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "This game isn't yours.",
                ephemeral=True,
            )
            return False
        return True

    async def _play(self, interaction: discord.Interaction, player_move: str):
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]

        bot_move = random.choice(["rock", "paper", "scissors"])
        pe, be = _RPS_EMOJI[player_move], _RPS_EMOJI[bot_move]

        if player_move == bot_move:
            result = "🤝 Tie!"
            coin_delta = 0
            color = GAME_COLOR
        elif _RPS_WINS[player_move] == bot_move:
            payout = self.bet if self.bet else _FREE_WIN
            result = f"🎉 You win! +{payout} 🪙"
            coin_delta = payout
            color = SUCCESS_COLOR
        else:
            loss = -self.bet if self.bet else 0
            result = f"😞 Bot wins. {loss} 🪙" if self.bet else "😞 Bot wins."
            coin_delta = loss
            color = ERROR_COLOR

        # Single-player RPS: bet was not pre-deducted, outcome is applied
        # directly. Positive coin_delta = win (credit), negative = loss (debit
        # with overdraft to preserve the original floor-at-zero behaviour).
        if coin_delta > 0:
            new_bal = await economy_service.credit(
                self.guild_id,
                self.user.id,
                coin_delta,
                reason="rps:solo_win",
                actor_id=self.user.id,
            )
        elif coin_delta < 0:
            new_bal = await economy_service.debit(
                self.guild_id,
                self.user.id,
                -coin_delta,
                reason="rps:solo_loss",
                actor_id=self.user.id,
                allow_overdraft=True,
            )
        else:
            new_bal = await global_db.get_coins(self.user.id, self.guild_id)
        embed = discord.Embed(
            title="✂️ Rock · Paper · Scissors",
            description=(
                f"You: **{player_move}** {pe}  vs  Bot: **{bot_move}** {be}\n\n"
                f"{result}\n"
                f"Balance: **{new_bal}** 🪙"
            ),
            color=color,
        )
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    @discord.ui.button(label="Rock", emoji="🪨", style=discord.ButtonStyle.grey)
    async def rock(self, i: discord.Interaction, _: discord.ui.Button):
        await self._play(i, "rock")

    @discord.ui.button(label="Paper", emoji="📄", style=discord.ButtonStyle.grey)
    async def paper(self, i: discord.Interaction, _: discord.ui.Button):
        await self._play(i, "paper")

    @discord.ui.button(label="Scissors", emoji="✂️", style=discord.ButtonStyle.grey)
    async def scissors(self, i: discord.Interaction, _: discord.ui.Button):
        await self._play(i, "scissors")

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        try:
            await self.message.edit(content="Game timed out.", view=self)
        except Exception:
            pass
