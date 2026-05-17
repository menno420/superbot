"""RPS tournament subsystem — pure rules + helpers + persistence (S4.4 + S4.6).

See ``docs/architecture.md`` §"Subsystem decomposition" for the layout
convention.  Modules in this package are pure-ish (no cog state, no
Discord-API I/O) except where noted.

Modules:
    rules         — move alias map, game-mode whitelist, win-condition
                    table, ``normalize_move``, ``determine_winner``
                    (S4.4; consumed by handle_bot_match_move + on_message
                    + resolve_match)
    _persistence  — game_state_service writers and recovery helpers for
                    rps_pvp_pending + rps_tournament subsystems (S4.6)
    _helpers      — channel-creation + stat-update + lifecycle-task
                    helpers shared between bot-match and tournament
                    code paths (S4.6)
    _bot_matches  — module-level state (_bot_matches, _bot_match_channels)
                    + bot-vs-player command/handler bodies (S4.6).
                    State is initialised by the cog's __init__ and
                    cleared by cog_unload so reload semantics match
                    the pre-extraction layout.
"""
