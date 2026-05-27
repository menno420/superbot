"""Blackjack solo/PvP-hand view (S4.5).

``BlackjackView`` drives both solo blackjack (vs. dealer) and the
per-player half of a PvP match.  PvP coordination is done via an
``on_finish`` callback supplied by ``_start_pvp``.  Tournament rounds
use a separate view (``_TournBlackjackView``) because the chip / round
bookkeeping differs.

Solo end-of-hand UX: when a solo hand finishes (i.e. no PvP
``on_finish`` callback and no ``tournament_chips``), ``_finish`` swaps
the live ``BlackjackView`` for a fresh ``_BlackjackSoloResultView`` —
the same disabled hit/stand/double shells on row 0, plus enabled
``🔁 Play again`` / ``◀ Back to Blackjack`` on row 1.  Replacing
the view (instead of appending buttons and calling ``stop()`` on the
original) keeps the terminal-state buttons dispatchable: the original
view's stop unregisters its callbacks from discord.py, and any
buttons still bound to it would fail to respond. PvP and tournament
paths keep their original ``BlackjackView`` until ``stop()`` — they
never expose replay/back.
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

        # Solo-only: hand the message off to a fresh result view so the
        # Play again / Back buttons remain dispatchable. Calling
        # self.stop() on a view that still exposes enabled buttons
        # un-registers it from discord.py's dispatch table — those
        # buttons would then surface "interaction failed" on click.
        if self.game.tournament_chips is None and self.on_finish is None:
            result_view = _BlackjackSoloResultView(
                self.game.user_id,
                self.game.guild_id,
                self.game.bet,
                self.game,
            )
            await safe_edit(interaction, embed=embed, view=result_view)
            result_view.message = interaction.message
        else:
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
            item.disabled = True  # type: ignore[attr-defined]
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
        # Defer up front — _save_game_state below races the 3 s
        # interaction token once the I/O completes.
        if not await safe_defer(interaction):
            return
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
        await safe_edit(interaction, embed=_game_embed(self.game), view=self)

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


class _BlackjackSoloResultView(discord.ui.View):
    """Terminal-state view shown after a solo blackjack hand resolves.

    Replaces the live ``BlackjackView`` once ``_finish`` settles so that
    Play again / Back buttons stay independently dispatchable. The
    previous design appended these buttons to the still-attached
    ``BlackjackView`` and called ``self.stop()`` — which removes the
    view from discord.py's component dispatch table and leaves the
    visible buttons unable to respond (Discord then renders
    "interaction failed" after the 3 s response window).
    """

    def __init__(
        self,
        user_id: int,
        guild_id: int,
        bet: int,
        game: _Game | None,
    ) -> None:
        super().__init__(timeout=120)
        self.user_id = user_id
        self.guild_id = guild_id
        self.bet = bet
        self.game = game
        self.message: discord.Message | None = None

        for label, emoji, style in (
            ("Hit", "👊", discord.ButtonStyle.green),
            ("Stand", "✋", discord.ButtonStyle.grey),
            ("Double Down", "✌️", discord.ButtonStyle.blurple),
        ):
            self.add_item(
                discord.ui.Button(
                    label=label,
                    emoji=emoji,
                    style=style,
                    disabled=True,
                    row=0,
                ),
            )

        replay_btn = discord.ui.Button(  # type: ignore[var-annotated]
            label="🔁 Play again",
            style=discord.ButtonStyle.success,
            custom_id="blackjack:solo:replay",
            row=1,
        )
        replay_btn.callback = self._replay  # type: ignore[method-assign]
        self.add_item(replay_btn)

        # Late import: blackjack_panel imports BlackjackView indirectly
        # via the actions helpers, so importing it at module level
        # would create a cycle.
        from views.games.blackjack_panel import _make_blackjack_back_button

        back_btn = _make_blackjack_back_button()
        back_btn.row = 1
        self.add_item(back_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This isn't your hand.",
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
        except Exception:
            pass

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,  # type: ignore[type-arg]
    ) -> None:
        await _on_view_error(self, interaction, error, item)

    async def _replay(self, interaction: discord.Interaction) -> None:
        """Re-enter ``start_solo_blackjack`` with the same user/guild/bet.

        Delegates to the canonical solo entry point so the active-game
        map (``_active``), persistence, and natural-blackjack auto-payout
        behave identically to a fresh ``!blackjack`` invocation. Balance
        is checked inside ``start_solo_blackjack``; insufficient balance
        surfaces as an ephemeral nudge here.
        """
        if not await safe_defer(interaction):
            return

        # Late imports — actions imports BlackjackView at module level.
        from cogs.blackjack.actions import (
            commit_solo_blackjack,
            start_solo_blackjack,
        )

        user = interaction.user
        guild = interaction.guild
        if guild is None:
            await safe_followup(
                interaction,
                "❌ Replay isn't available in DMs.",
                ephemeral=True,
            )
            return

        result = await start_solo_blackjack(
            user,
            guild,
            interaction.channel,  # type: ignore[arg-type]
            self.bet,
        )
        if result.ephemeral_message is not None:
            await safe_followup(
                interaction,
                result.ephemeral_message,
                ephemeral=True,
            )
            return

        # Natural blackjack auto-payout path: short-circuits with an
        # embed but no playable view. Render the result and stop here.
        if result.view is None:
            await safe_edit(interaction, embed=result.embed, view=None)
            return

        await safe_edit(interaction, embed=result.embed, view=result.view)
        await commit_solo_blackjack(result.view, interaction.message)  # type: ignore[arg-type]
