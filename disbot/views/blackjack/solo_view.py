"""Blackjack solo/PvP-hand view (S4.5).

``BlackjackView`` drives both solo blackjack (vs. dealer) and the
per-player half of a PvP match.  PvP coordination is done via an
``on_finish`` callback supplied by ``_start_pvp``.  Tournament rounds
use a separate view (``_TournBlackjackView``) because the chip / round
bookkeeping differs.
"""

from __future__ import annotations

import discord

from cogs.blackjack._persistence import _clear_solo_game, _save_game_state
from cogs.blackjack._state import FREE_WIN_COINS, _active, _Game
from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup
from services import economy_service
from services.blackjack_engine import hand_value as _hand_value
from services.blackjack_engine import is_blackjack as _is_blackjack
from utils import db
from utils.ui_constants import ECONOMY_COLOR, ERROR_COLOR, GAME_COLOR, SUCCESS_COLOR
from views.base import handle_view_error as _on_view_error
from views.blackjack.embeds import _game_embed


class BlackjackView(discord.ui.View):
    def __init__(self, game: _Game, on_finish=None):
        super().__init__(timeout=120)
        self.game = game
        self.on_finish = on_finish  # async callback(game, outcome_value)
        self.message: discord.Message | None = None
        self.double_btn.disabled = game.bet == 0 or game.tournament_chips is not None

    async def _finish(
        self,
        interaction: discord.Interaction,
        result: str,
        color: discord.Color,
        coin_delta: int,
        hand_value: int,
    ):
        # Idempotent defer — protects the chain hit_btn/stand_btn/double_btn →
        # _resolve → _finish, where balance writes precede the message edit.
        if not await safe_defer(interaction):
            return
        key = (self.game.user_id, self.game.guild_id)
        _active.pop(key, None)
        await _clear_solo_game(self.game)  # PR G2 — game ended naturally
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]

        embed = _game_embed(self.game, reveal=True)
        embed.color = color

        if self.game.tournament_chips is None:
            # Solo blackjack: bet is not pre-escrowed, the outcome delta
            # is applied directly. Sign decides credit vs debit; loss
            # path keeps overdraft-tolerant flooring to preserve prior
            # add_coins(GREATEST(0, …)) semantics.
            if coin_delta > 0:
                new_bal = await economy_service.credit(
                    self.game.guild_id,
                    self.game.user_id,
                    coin_delta,
                    reason="blackjack:solo_win",
                    actor_id=self.game.user_id,
                )
            elif coin_delta < 0:
                new_bal = await economy_service.debit(
                    self.game.guild_id,
                    self.game.user_id,
                    -coin_delta,
                    reason="blackjack:solo_loss",
                    actor_id=self.game.user_id,
                    allow_overdraft=True,
                )
            else:
                new_bal = await db.get_coins(
                    self.game.user_id,
                    self.game.guild_id,
                )
            delta_str = f"+{coin_delta}" if coin_delta >= 0 else str(coin_delta)
            embed.add_field(
                name=result,
                value=f"{delta_str} 🪙  |  Balance: **{new_bal}** 🪙",
                inline=False,
            )
        else:
            embed.add_field(name=result, value="​", inline=False)

        await safe_edit(interaction, embed=embed, view=self)
        self.stop()

        if self.on_finish:
            await self.on_finish(self.game, hand_value)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.game.user_id:
            await interaction.response.send_message(
                "This isn't your hand.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self):
        _active.pop((self.game.user_id, self.game.guild_id), None)
        await _clear_solo_game(self.game)  # PR G2 — abandoned
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(content="Game timed out.", view=self)
        except Exception:
            pass
        if self.on_finish:
            await self.on_finish(self.game, -1)  # treat as bust on timeout

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,  # type: ignore[type-arg]
    ) -> None:
        await _on_view_error(self, interaction, error, item)

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.green, emoji="👊")
    async def hit_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        self.game.hit()
        pv = _hand_value(self.game.player)
        if pv > 21:
            effective = self.game.bet * 2 if self.game.doubled else self.game.bet
            await self._finish(
                interaction,
                "💥 Bust — you lose!",
                ERROR_COLOR,
                -effective if effective else 0,
                -1,
            )
            return
        # PR G2/G3 — persist post-hit state.  Solo writes to
        # blackjack_solo; PvP writes the whole match to blackjack_pvp.
        # ``cog_load`` will clear either kind on next restart.
        await _save_game_state(self.game)
        self.double_btn.disabled = True
        await interaction.response.edit_message(embed=_game_embed(self.game), view=self)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.grey, emoji="✋")
    async def stand_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._resolve(interaction)

    @discord.ui.button(
        label="Double Down",
        style=discord.ButtonStyle.blurple,
        emoji="✌️",
    )
    async def double_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        bal = await db.get_coins(self.game.user_id, self.game.guild_id)
        if bal < self.game.bet * 2:
            await safe_followup(
                interaction,
                f"❌ Need {self.game.bet * 2} 🪙 to double (you have {bal}).",
                ephemeral=True,
            )
            return
        self.game.hit()
        self.game.doubled = True
        if _hand_value(self.game.player) > 21:
            await self._finish(
                interaction,
                "💥 Bust — you lose!",
                ERROR_COLOR,
                -(self.game.bet * 2),
                -1,
            )
            return
        # PR G2/G3 — persist post-double state.  ``_resolve`` will
        # finish synchronously and clear, but if the bot crashes
        # mid-resolve the saved state survives and ``cog_load`` will
        # discard it.
        await _save_game_state(self.game)
        await self._resolve(interaction)

    async def _resolve(self, interaction: discord.Interaction):
        self.game.dealer_play()
        pv = _hand_value(self.game.player)
        dv = _hand_value(self.game.dealer)
        effective = self.game.bet * 2 if self.game.doubled else self.game.bet

        if _is_blackjack(self.game.player):
            payout = int(effective * 1.5) if effective else FREE_WIN_COINS
            await self._finish(interaction, "🎉 Blackjack!", ECONOMY_COLOR, payout, pv)
        elif dv > 21:
            payout = effective if effective else FREE_WIN_COINS
            await self._finish(
                interaction,
                "🎉 Dealer busts — you win!",
                SUCCESS_COLOR,
                payout,
                pv,
            )
        elif pv > dv:
            payout = effective if effective else FREE_WIN_COINS
            await self._finish(interaction, "🎉 You win!", SUCCESS_COLOR, payout, pv)
        elif pv == dv:
            await self._finish(interaction, "🤝 Push — tie.", GAME_COLOR, 0, pv)
        else:
            loss = -effective if effective else 0
            await self._finish(interaction, "😞 Dealer wins.", ERROR_COLOR, loss, pv)
