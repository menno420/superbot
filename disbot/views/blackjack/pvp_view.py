"""Blackjack PvP challenge + match orchestration (S4.5).

The challenge view collects accept/decline from the opponent.  When
accepted, ``_start_pvp`` deals both hands and creates the per-player
``BlackjackView`` instances.  ``_resolve_pvp`` runs once both players
finish (or both natural-blackjack out) and applies the bet-swap.
"""

from __future__ import annotations

import discord

from cogs.blackjack._persistence import _clear_pvp_match, _save_pvp_match
from cogs.blackjack._state import FREE_WIN_COINS, _active, _Game, _pvp, _PvPState
from core.runtime.interaction_helpers import safe_edit
from services import economy_service
from services.blackjack_engine import is_blackjack as _is_blackjack
from utils.ui_constants import ECONOMY_COLOR, GAME_COLOR
from views.base import handle_view_error as _on_view_error
from views.blackjack.embeds import _game_embed
from views.blackjack.solo_view import BlackjackView


class _ChallengeView(discord.ui.View):
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
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        # Bail if the edit fails: _start_pvp deals both hands and sends
        # per-player messages to the channel — if the accept edit was
        # rejected by Discord (token expired, channel gone) we'd end up
        # with two live blackjack hands and no acknowledged challenge.
        if not await safe_edit(
            interaction,
            content="✅ Challenge accepted — dealing hands…",
            view=self,
        ):
            return
        self.stop()
        await _start_pvp(
            interaction,
            self.challenger,
            self.opponent,
            self.guild_id,
            self.bet,
        )

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
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        try:
            await self.message.edit(content="⏰ Challenge timed out.", view=self)
        except Exception:
            pass

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,  # type: ignore[type-arg]
    ) -> None:
        await _on_view_error(self, interaction, error, item)


async def _start_pvp(
    interaction: discord.Interaction,
    p1: discord.Member,
    p2: discord.Member,
    guild_id: int,
    bet: int,
):
    channel = interaction.channel
    state = _PvPState(p1.id, p2.id, guild_id, bet, channel.id)
    key = frozenset({p1.id, p2.id})
    _pvp[key] = state

    for player in (p1, p2):
        uid = player.id
        gid = guild_id
        game = _Game(uid, gid, bet, channel_id=channel.id)
        game.pvp_peer_id = p2.id if uid == p1.id else p1.id
        game.pvp_state = state
        _active[(uid, gid)] = game

        if _is_blackjack(game.player):
            embed = _game_embed(
                game,
                reveal=True,
                title=f"🃏 {player.display_name}'s hand",
            )
            embed.color = ECONOMY_COLOR
            embed.add_field(
                name="Blackjack!",
                value="Waiting for opponent…",
                inline=False,
            )
            msg = await channel.send(content=player.mention, embed=embed)  # type: ignore[union-attr]
            state.messages[uid] = msg
            state.results[uid] = 21
            _active.pop((uid, gid), None)
        else:

            async def _pvp_finish(
                g: _Game,
                hand_val: int,
                _player=player,
                _state=state,
            ):
                _state.results[g.user_id] = hand_val
                if len(_state.results) == 2:
                    await _resolve_pvp(_state, channel)  # type: ignore[arg-type]

            view = BlackjackView(game, on_finish=_pvp_finish)
            embed = _game_embed(game, title=f"🃏 {player.display_name}'s hand")
            msg = await channel.send(content=player.mention, embed=embed, view=view)  # type: ignore[union-attr]
            view.message = msg
            state.messages[uid] = msg

    # PR G3 — initial PvP match save once both views are live (or
    # both players hit natural blackjack and we're about to resolve).
    await _save_pvp_match(state)

    # If both got instant blackjack
    if len(state.results) == 2:
        await _resolve_pvp(state, channel)  # type: ignore[arg-type]


async def _resolve_pvp(state: _PvPState, channel: discord.TextChannel):
    key = frozenset({state.p1, state.p2})
    _pvp.pop(key, None)
    # PR G3 — match is fully resolved; drop the persisted row.
    # Settlement-side credit/debit runs below regardless of the clear
    # result, so a clear failure is non-fatal (the 24h game_state GC
    # will sweep eventually).
    await _clear_pvp_match(state)

    v1 = state.results.get(state.p1, -1)
    v2 = state.results.get(state.p2, -1)

    if v1 == -1 and v2 == -1:
        result = "🤝 Both busted — tie! No coins exchanged."
        coin_change = 0
        winner_id = None
    elif v1 == -1:
        winner_id = state.p2
        result = f"<@{state.p2}> wins (opponent busted)!"
        coin_change = state.bet
    elif v2 == -1:
        winner_id = state.p1
        result = f"<@{state.p1}> wins (opponent busted)!"
        coin_change = state.bet
    elif v1 > v2:
        winner_id = state.p1
        result = f"<@{state.p1}> wins with **{v1}** vs **{v2}**!"
        coin_change = state.bet
    elif v2 > v1:
        winner_id = state.p2
        result = f"<@{state.p2}> wins with **{v2}** vs **{v1}**!"
        coin_change = state.bet
    else:
        result = f"🤝 Tie — both had **{v1}**. No coins exchanged."
        coin_change = 0
        winner_id = None

    if coin_change and winner_id:
        loser_id = state.p2 if winner_id == state.p1 else state.p1
        payout = coin_change if coin_change else FREE_WIN_COINS
        # Two-side payout: preserve prior add_coins floor-at-zero
        # semantics for the loser (overdraft permitted). See the
        # matching RPS PvP comment for the bet-escrow follow-up.
        await economy_service.credit(
            state.guild_id,
            winner_id,
            payout,
            reason="blackjack:pvp_win",
        )
        await economy_service.debit(
            state.guild_id,
            loser_id,
            payout,
            reason="blackjack:pvp_loss",
            allow_overdraft=True,
        )

    embed = discord.Embed(
        title="🃏 Blackjack PvP Result",
        description=result,
        color=ECONOMY_COLOR if winner_id else GAME_COLOR,
    )
    embed.add_field(
        name=f"<@{state.p1}>",
        value=f"**{v1 if v1 >= 0 else 'Bust'}**",
        inline=True,
    )
    embed.add_field(
        name=f"<@{state.p2}>",
        value=f"**{v2 if v2 >= 0 else 'Bust'}**",
        inline=True,
    )
    await channel.send(embed=embed)
