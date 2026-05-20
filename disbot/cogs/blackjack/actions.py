"""Blackjack action helpers (PR 5).

Shared helpers used by the playable Help/Games → Blackjack panel
(``views.games.blackjack_panel``). The cog's typed-command bodies
(``!blackjack``, ``!bjtournament``) remain authoritative; these
helpers wrap the same engine state (``_Game``, ``_active``,
``_pvp``, ``_tournaments``) so the panel buttons run identical
gameplay logic without duplicating it.

Three entry points:

* :func:`start_solo_blackjack` — solo vs dealer (used by Solo Free
  Play / Solo Bet buttons).
* :func:`build_blackjack_challenge_view` — PvP challenge spawner
  (used by Challenge Player button).
* :func:`open_blackjack_tournament` — admin tournament setup (used
  by Tournament → Open Registration button).

Each helper returns the (embed, view, message_text) tuple the panel
edit_message call needs. The auto-payout "natural blackjack" path
returns ``view=None`` so the panel knows not to attach the playable
view.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import discord
from discord.ext import commands

from cogs.blackjack._persistence import _save_game_state
from cogs.blackjack._state import (
    FREE_WIN_COINS,
    _active,
    _BjTournament,
    _Game,
    _pvp,
    _tournaments,
)
from core.runtime import tasks
from services import economy_service, tournament_state_service
from services.blackjack_engine import is_blackjack as _is_blackjack
from utils import db
from utils.ui_constants import ECONOMY_COLOR, SUCCESS_COLOR
from views.blackjack.embeds import _game_embed, _tourn_embed
from views.blackjack.pvp_view import _ChallengeView
from views.blackjack.solo_view import BlackjackView
from views.blackjack.tournament_views import _TournRegistrationView


@dataclass
class SoloStartResult:
    """Return tuple for :func:`start_solo_blackjack`.

    ``view`` is ``None`` when the start short-circuited (already
    playing, insufficient balance, natural blackjack auto-payout). In
    that case ``ephemeral_message`` carries the user-facing reason for
    short-circuits and ``embed`` is set for the auto-payout path.
    ``game`` is set only when a playable hand was dealt — the caller
    is responsible for assigning ``view.message`` and calling
    :func:`_save_game_state` after the message edit succeeds.
    """

    embed: discord.Embed | None
    view: BlackjackView | None
    game: _Game | None
    ephemeral_message: str | None = None


async def start_solo_blackjack(
    user: discord.Member | discord.User,
    guild: discord.Guild,
    channel: discord.abc.MessageableChannel,
    bet: int,
) -> SoloStartResult:
    """Deal a fresh solo Blackjack hand, mirroring the ``!blackjack``
    body (cogs/blackjack_cog.py:405-488). No new state machinery; the
    same ``_Game``, ``_active`` dict, and persistence path.
    """
    if bet < 0:
        return SoloStartResult(
            None,
            None,
            None,
            ephemeral_message="Bet must be 0 or positive.",
        )
    key = (user.id, guild.id)
    if key in _active:
        return SoloStartResult(
            None,
            None,
            None,
            ephemeral_message="You already have a game running!",
        )
    if bet > 0:
        bal = await db.get_coins(user.id, guild.id)
        if bet > bal:
            return SoloStartResult(
                None,
                None,
                None,
                ephemeral_message=f"❌ You only have **{bal}** 🪙.",
            )

    game = _Game(user.id, guild.id, bet, channel_id=channel.id)
    _active[key] = game

    if _is_blackjack(game.player):
        payout = int(bet * 1.5) if bet else FREE_WIN_COINS
        new_bal = await economy_service.credit(
            guild.id,
            user.id,
            payout,
            reason="blackjack:natural_blackjack",
            actor_id=user.id,
        )
        embed = _game_embed(game, reveal=True)
        embed.color = ECONOMY_COLOR
        embed.add_field(
            name="🎉 Blackjack!",
            value=f"+{payout} 🪙  |  Balance: **{new_bal}** 🪙",
            inline=False,
        )
        _active.pop(key)
        return SoloStartResult(embed, None, None)

    return SoloStartResult(_game_embed(game), BlackjackView(game), game)


async def commit_solo_blackjack(view: BlackjackView, message: discord.Message) -> None:
    """Attach the message to the live view and persist the initial
    snapshot. Mirrors the cog command's post-send bookkeeping.
    """
    view.message = message
    await _save_game_state(view.game)


def build_blackjack_challenge_view(
    challenger: discord.Member,
    opponent: discord.Member,
    guild_id: int,
    bet: int,
) -> tuple[discord.Embed, _ChallengeView | None, str | None]:
    """Build the PvP challenge embed + view.

    Returns ``(embed, view, error_message)``. When ``error_message``
    is set, ``view`` is ``None`` and the caller should surface the
    message ephemerally (challenge target is invalid).
    """
    if opponent.id == challenger.id:
        return _empty_embed(), None, "You can't challenge yourself."
    if opponent.bot:
        return (
            _empty_embed(),
            None,
            "You can't challenge a bot to PvP.",
        )
    key = frozenset({challenger.id, opponent.id})
    if key in _pvp:
        return (
            _empty_embed(),
            None,
            "There's already a PvP game between these players.",
        )
    bet_str = f"**{bet}** 🪙" if bet else "free play"
    embed = discord.Embed(
        title="🃏 Blackjack Challenge!",
        description=(
            f"{challenger.mention} challenges {opponent.mention} to "
            f"Blackjack ({bet_str}).\n{opponent.mention}, do you accept?"
        ),
        color=SUCCESS_COLOR,
    )
    view = _ChallengeView(challenger, opponent, guild_id, bet)
    return embed, view, None


def _empty_embed() -> discord.Embed:
    """A placeholder embed for the error branch — never displayed,
    but lets the return tuple stay homogeneous.
    """
    return discord.Embed(title=" ", description=" ")


@dataclass
class TournamentStartResult:
    """Return tuple for :func:`open_blackjack_tournament`."""

    embed: discord.Embed | None
    view: _TournRegistrationView | None
    tournament: _BjTournament | None
    ephemeral_message: str | None = None


async def open_blackjack_tournament(
    host: discord.Member | discord.User,
    guild: discord.Guild,
    channel: discord.abc.MessageableChannel,
    bot: commands.Bot,
    *,
    entry_fee: int = 0,
    rounds: int = 5,
    duration_mins: int = 5,
) -> TournamentStartResult:
    """Spawn a Blackjack tournament registration window — same engine
    state as ``!bjtournament`` (cogs/blackjack_cog.py:490-538). The
    caller is responsible for adding the ✅ reaction and capturing the
    sent message on ``tourn.reg_message``.
    """
    from cogs.blackjack_cog import _launch_tournament  # local — avoid cycle

    if _tournaments.get(guild.id):
        return TournamentStartResult(
            None,
            None,
            None,
            ephemeral_message="A tournament is already running.",
        )
    existing = await tournament_state_service.get_active(guild.id)
    if existing:
        return TournamentStartResult(
            None,
            None,
            None,
            ephemeral_message=(
                f"A **{existing}** tournament is already active in this server."
            ),
        )
    if entry_fee < 0 or rounds < 1 or duration_mins < 1:
        return TournamentStartResult(
            None,
            None,
            None,
            ephemeral_message="Invalid parameters.",
        )

    tourn = _BjTournament(
        host.id,
        guild.id,
        channel.id,
        entry_fee,
        rounds,
        duration_mins,
    )
    _tournaments[guild.id] = tourn
    await tournament_state_service.set_active(guild.id, "blackjack")

    async def _auto_start():
        await asyncio.sleep(duration_mins * 60)
        if not tourn.started and tourn.guild_id in _tournaments:
            await _launch_tournament(tourn, guild, bot)

    tourn.timer_task = tasks.spawn(
        f"blackjack:autostart:{tourn.guild_id}",
        _auto_start(),
    )

    return TournamentStartResult(
        _tourn_embed(tourn),
        _TournRegistrationView(tourn),
        tourn,
    )


def get_active_tournament(guild_id: int) -> _BjTournament | None:
    """Return the currently registered Blackjack tournament for the
    guild, or ``None`` if no tournament is open.
    """
    return _tournaments.get(guild_id)


__all__ = [
    "SoloStartResult",
    "TournamentStartResult",
    "build_blackjack_challenge_view",
    "commit_solo_blackjack",
    "get_active_tournament",
    "open_blackjack_tournament",
    "start_solo_blackjack",
]
