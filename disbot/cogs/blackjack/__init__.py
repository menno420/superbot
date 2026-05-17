"""Blackjack subsystem — state + persistence + helpers (S4.5).

See ``docs/architecture.md`` §"Subsystem decomposition" for the layout
convention.  Modules in this package contain blackjack domain state
and persistence that the cog uses, the views import, and tests
exercise directly.

Modules:
    _state        — data classes (_Game, _PvPState, _BjTournament,
                    _TournPlayerState), module-level state dicts
                    (_active, _pvp, _tournaments), and the public
                    constants (FREE_WIN_COINS, TOURN_*, BLACKJACK_*).
    _persistence  — game_state_service writers and clearers for the
                    three blackjack subsystems (solo / pvp /
                    tournament).  Also hosts the small predicates
                    (_is_solo_game) and serialization helpers
                    (_serialize_pvp_hand, _pvp_canonical_user_id).

cogs/blackjack_cog.py re-exports every public name from both modules
so existing tests (``from cogs.blackjack_cog import _Game, ...``) keep
resolving.  Patch sites (``patch('cogs.blackjack_cog.X')``) need to
target the actual defining module
(``cogs.blackjack._state`` or ``cogs.blackjack._persistence``); the
test files updated in this PR were migrated as part of the
extraction.
"""
