"""Blackjack embed builders (S4.5).

Pure-ish embed factories used by the four view classes and by the
tournament registration / round flows.  No Discord I/O, no DB reads
— just embed construction.
"""

from __future__ import annotations

import discord

from services.blackjack_engine import hand_str as _hand_str
from services.blackjack_engine import hand_value as _hand_value
from services.blackjack_engine import rank_value as _rank_value
from services.blackjack_state import (
    FREE_WIN_COINS,
    TOURN_BET_PER_ROUND,
    _BjTournament,
    _Game,
)
from utils.ui_constants import SUCCESS_COLOR


def _game_embed(
    game: _Game,
    reveal: bool = False,
    title: str = "🃏 Blackjack",
) -> discord.Embed:
    pv = _hand_value(game.player)
    if reveal:
        dv = _hand_value(game.dealer)
        d_str = _hand_str(game.dealer)
        d_lbl = f"Dealer ({dv})"
    else:
        d_str = _hand_str(game.dealer, hide_second=True)
        d_lbl = f"Dealer ({_rank_value(game.dealer[0].split()[0])}+?)"

    bet_str = f"**{game.bet}** 🪙" if game.bet else f"Free (win = +{FREE_WIN_COINS} 🪙)"
    if game.tournament_chips is not None:
        bet_str = f"Tournament chips: **{game.tournament_chips}** | Bet: {TOURN_BET_PER_ROUND}"

    embed = discord.Embed(title=title, color=SUCCESS_COLOR)
    embed.add_field(name=d_lbl, value=d_str, inline=False)
    embed.add_field(
        name=f"Your hand ({pv})",
        value=_hand_str(game.player),
        inline=False,
    )
    embed.add_field(name="Bet", value=bet_str, inline=True)
    return embed


def _tourn_embed(t: _BjTournament) -> discord.Embed:
    fee_str = f"**{t.entry_fee}** 🪙" if t.entry_fee else "Free"
    embed = discord.Embed(
        title="🃏 Blackjack Tournament — Registration Open",
        color=SUCCESS_COLOR,
    )
    embed.add_field(name="Entry Fee", value=fee_str, inline=True)
    embed.add_field(name="Rounds", value=str(t.rounds), inline=True)
    embed.add_field(name="Duration", value=f"{t.duration_mins} min", inline=True)
    embed.add_field(name="Players", value=str(len(t.players)), inline=True)
    embed.add_field(name="Pot", value=f"{t.pot} 🪙", inline=True)
    embed.set_footer(text="React ✅ or click Join to register.")
    return embed


async def _update_tourn_embed(t: _BjTournament):
    """Edit the tournament registration message in place when a player joins."""
    if not t.reg_message:
        return
    embed = _tourn_embed(t)
    try:
        await t.reg_message.edit(embed=embed)
    except Exception:
        pass
