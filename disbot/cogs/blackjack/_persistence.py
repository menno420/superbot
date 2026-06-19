"""Blackjack persistence — back-compat re-export shim (fleet unit A3).

The canonical home is now :mod:`services.blackjack_persistence`.  This
module re-exports the leaf helpers and keeps a ``game_state_service``
attribute so the existing test suite — which patches
``cogs.blackjack._persistence.game_state_service.save`` /
``…game_state_service.clear`` (a method on the shared ``game_state_service``
module) and ``cogs.blackjack._persistence._save_solo_game`` /
``…_save_pvp_match`` (the leaf functions the dispatcher below looks up) —
keeps working without changes.

``_save_game_state`` is re-defined here (rather than re-exported) so it
resolves ``_save_solo_game`` / ``_save_pvp_match`` / ``_is_solo_game`` in
*this* module's namespace.  That keeps the routing test
(``patch('cogs.blackjack._persistence._save_solo_game')``) effective for
the cog's call path; the ``services.blackjack_persistence`` copy is the
one the view layer uses.  Both dispatchers are behaviorally identical.

New code should import directly from :mod:`services.blackjack_persistence`.
"""

from __future__ import annotations

from services import game_state_service  # noqa: F401 — back-compat patch target
from services.blackjack_persistence import (  # noqa: F401 — re-exported
    _clear_pvp_match,
    _clear_solo_game,
    _clear_tournament_entry,
    _is_solo_game,
    _pvp_canonical_user_id,
    _save_pvp_match,
    _save_solo_game,
    _save_tournament_entry,
    _serialize_pvp_hand,
)
from services.blackjack_state import _Game


async def _save_game_state(game: _Game) -> None:
    """Dispatch a save to the right subsystem helper based on game type.

    Re-defined here (vs. re-exported) so the ``_save_solo_game`` /
    ``_save_pvp_match`` lookups hit *this* module's namespace — that
    keeps ``patch('cogs.blackjack._persistence._save_solo_game')`` (the
    routing test) effective for the cog's call path.
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


__all__ = [
    "_clear_pvp_match",
    "_clear_solo_game",
    "_clear_tournament_entry",
    "_is_solo_game",
    "_pvp_canonical_user_id",
    "_save_game_state",
    "_save_pvp_match",
    "_save_solo_game",
    "_save_tournament_entry",
    "_serialize_pvp_hand",
    "game_state_service",
]
