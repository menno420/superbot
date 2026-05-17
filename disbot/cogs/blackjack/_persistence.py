"""Blackjack persistence helpers (S4.5).

Each helper here corresponds to one of the three blackjack subsystems
(solo / pvp / tournament).  All writes go through
``services.game_state_service``, which is the single mutation surface
for game_state rows (per the layer rules in docs/ownership.md).

The pre-extraction layout had these in ``cogs/blackjack_cog.py``; this
module is a pure relocation.  Test patches that previously targeted
``cogs.blackjack_cog.game_state_service.X`` should now target
``cogs.blackjack._persistence.game_state_service.X`` — the function
looks up ``game_state_service`` in its own module's namespace, so
that's where the patch must apply.
"""

from __future__ import annotations

import logging

from cogs.blackjack._state import (
    BLACKJACK_PVP_SUBSYSTEM,
    BLACKJACK_PVP_VERSION,
    BLACKJACK_SOLO_SUBSYSTEM,
    BLACKJACK_SOLO_VERSION,
    BLACKJACK_TOURNAMENT_SUBSYSTEM,
    BLACKJACK_TOURNAMENT_VERSION,
    _active,
    _Game,
    _PvPState,
)
from services import game_state_service

logger = logging.getLogger("bot")


def _is_solo_game(game: _Game) -> bool:
    return game.pvp_peer_id is None and game.tournament_chips is None


# ---------------------------------------------------------------------------
# Solo
# ---------------------------------------------------------------------------


async def _save_solo_game(game: _Game) -> None:
    """Save the in-progress solo blackjack hand to game_state.

    Skips non-solo games (PvP / tournament have their own subsystems).
    Failures are logged WARN but never block gameplay — the in-memory
    ``_active`` dict is authoritative while the bot is alive.
    """
    if not _is_solo_game(game):
        return
    if game.channel_id is None:
        return
    try:
        await game_state_service.save(
            guild_id=game.guild_id,
            user_id=game.user_id,
            channel_id=game.channel_id,
            subsystem=BLACKJACK_SOLO_SUBSYSTEM,
            state={
                "bet": game.bet,
                "doubled": game.doubled,
                "deck": list(game.deck),
                "player": list(game.player),
                "dealer": list(game.dealer),
            },
            version=BLACKJACK_SOLO_VERSION,
        )
    except Exception as exc:
        logger.warning("blackjack_solo save failed: %s", exc)


async def _clear_solo_game(game: _Game) -> None:
    """Drop the persisted solo row when the game ends or times out."""
    if not _is_solo_game(game):
        return
    if game.channel_id is None:
        return
    try:
        await game_state_service.clear(
            guild_id=game.guild_id,
            user_id=game.user_id,
            channel_id=game.channel_id,
            subsystem=BLACKJACK_SOLO_SUBSYSTEM,
        )
    except Exception as exc:
        logger.warning("blackjack_solo clear failed: %s", exc)


# ---------------------------------------------------------------------------
# PvP
# ---------------------------------------------------------------------------


def _pvp_canonical_user_id(p1_id: int, p2_id: int) -> int:
    """Single canonical user id used as the natural-key surrogate for
    a PvP match.  Matches the convention from PR G1 (RPS PvP) so the
    JSONB convention "smaller id wins the slot" is consistent across
    paired-state subsystems.
    """
    return min(p1_id, p2_id)


def _serialize_pvp_hand(game: _Game | None) -> dict | None:
    """Compact JSON-safe snapshot of one player's hand, or None if the
    player has already been popped from ``_active`` (i.e. they
    finished and the other player is still playing).
    """
    if game is None:
        return None
    return {
        "bet": game.bet,
        "doubled": game.doubled,
        "deck": list(game.deck),
        "player": list(game.player),
        "dealer": list(game.dealer),
    }


async def _save_pvp_match(state: _PvPState) -> None:
    """Best-effort persist of a PvP match's full state."""
    if state.channel_id is None:
        return
    p1_game = _active.get((state.p1, state.guild_id))
    p2_game = _active.get((state.p2, state.guild_id))
    try:
        await game_state_service.save(
            guild_id=state.guild_id,
            user_id=_pvp_canonical_user_id(state.p1, state.p2),
            channel_id=state.channel_id,
            subsystem=BLACKJACK_PVP_SUBSYSTEM,
            state={
                "p1_id": state.p1,
                "p2_id": state.p2,
                "bet": state.bet,
                # JSON-safe int keys.
                "results": {str(uid): v for uid, v in state.results.items()},
                "p1_game": _serialize_pvp_hand(p1_game),
                "p2_game": _serialize_pvp_hand(p2_game),
            },
            version=BLACKJACK_PVP_VERSION,
        )
    except Exception as exc:
        logger.warning("blackjack_pvp save failed: %s", exc)


async def _clear_pvp_match(state: _PvPState) -> None:
    """Best-effort game_state delete for a finished PvP match."""
    if state.channel_id is None:
        return
    try:
        await game_state_service.clear(
            guild_id=state.guild_id,
            user_id=_pvp_canonical_user_id(state.p1, state.p2),
            channel_id=state.channel_id,
            subsystem=BLACKJACK_PVP_SUBSYSTEM,
        )
    except Exception as exc:
        logger.warning("blackjack_pvp clear failed: %s", exc)


# ---------------------------------------------------------------------------
# Mode-dispatching wrapper (called by views)
# ---------------------------------------------------------------------------


async def _save_game_state(game: _Game) -> None:
    """Dispatch a save to the right subsystem helper based on game type.

    Solo, PvP, and tournament games run through the same
    ``BlackjackView`` so the call sites in ``hit_btn`` / ``double_btn``
    don't know which subsystem to write.  This dispatcher keeps the
    view code agnostic.
    """
    if game.pvp_state is not None:
        await _save_pvp_match(game.pvp_state)
    elif _is_solo_game(game):
        await _save_solo_game(game)
    # Tournament games carry their own per-player rows persisted by
    # ``_save_tournament_entry`` at launch time; per-hand state inside
    # a tournament round is intentionally NOT persisted — recovery is
    # cancel-and-refund (Option 2), so cards in flight don't matter
    # but the entry fee does.


# ---------------------------------------------------------------------------
# Tournament
# ---------------------------------------------------------------------------


async def _save_tournament_entry(
    *,
    guild_id: int,
    user_id: int,
    channel_id: int,
    entry_fee: int,
    rounds: int,
) -> None:
    """Persist the post-deduct_fees state for one tournament player."""
    try:
        await game_state_service.save(
            guild_id=guild_id,
            user_id=user_id,
            channel_id=channel_id,
            subsystem=BLACKJACK_TOURNAMENT_SUBSYSTEM,
            state={
                "bet": entry_fee,  # GC sweep refund convention
                "rounds": rounds,
            },
            version=BLACKJACK_TOURNAMENT_VERSION,
        )
    except Exception as exc:
        logger.warning(
            "blackjack_tournament save failed (user=%d guild=%d): %s",
            user_id,
            guild_id,
            exc,
        )


async def _clear_tournament_entry(
    *,
    guild_id: int,
    user_id: int,
    channel_id: int,
) -> None:
    """Drop a tournament player's persisted entry after natural completion."""
    try:
        await game_state_service.clear(
            guild_id=guild_id,
            user_id=user_id,
            channel_id=channel_id,
            subsystem=BLACKJACK_TOURNAMENT_SUBSYSTEM,
        )
    except Exception as exc:
        logger.warning(
            "blackjack_tournament clear failed (user=%d guild=%d): %s",
            user_id,
            guild_id,
            exc,
        )
