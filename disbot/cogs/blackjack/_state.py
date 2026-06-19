"""Blackjack state — back-compat re-export shim (fleet unit A3).

The canonical home is now :mod:`services.blackjack_state`.  This module
re-exports every public name so that ``cogs.blackjack_cog`` and the test
suite (``from cogs.blackjack._state import _active, _Game, …``) keep
resolving to the *same objects* — re-import preserves identity, so the
module-level state dicts (``_active`` / ``_pvp`` / ``_tournaments``) remain
the single shared instances the cog mutates and the views read.

New code should import directly from :mod:`services.blackjack_state`; this
shim exists only to avoid touching the (untouched) cog module and the
existing tests.
"""

from __future__ import annotations

from services.blackjack_state import (  # noqa: F401 — re-exported
    BLACKJACK_PVP_ESCROW_SUBSYSTEM,
    BLACKJACK_PVP_ESCROW_VERSION,
    BLACKJACK_PVP_SUBSYSTEM,
    BLACKJACK_PVP_VERSION,
    BLACKJACK_SOLO_SUBSYSTEM,
    BLACKJACK_SOLO_VERSION,
    BLACKJACK_TOURNAMENT_SUBSYSTEM,
    BLACKJACK_TOURNAMENT_VERSION,
    FREE_WIN_COINS,
    TOURN_BET_PER_ROUND,
    TOURN_START_CHIPS,
    _active,
    _BjTournament,
    _Game,
    _pvp,
    _PvPState,
    _tournaments,
    _TournPlayerState,
)

__all__ = [
    "BLACKJACK_PVP_ESCROW_SUBSYSTEM",
    "BLACKJACK_PVP_ESCROW_VERSION",
    "BLACKJACK_PVP_SUBSYSTEM",
    "BLACKJACK_PVP_VERSION",
    "BLACKJACK_SOLO_SUBSYSTEM",
    "BLACKJACK_SOLO_VERSION",
    "BLACKJACK_TOURNAMENT_SUBSYSTEM",
    "BLACKJACK_TOURNAMENT_VERSION",
    "FREE_WIN_COINS",
    "TOURN_BET_PER_ROUND",
    "TOURN_START_CHIPS",
    "_Game",
    "_PvPState",
    "_BjTournament",
    "_TournPlayerState",
    "_active",
    "_pvp",
    "_tournaments",
]
