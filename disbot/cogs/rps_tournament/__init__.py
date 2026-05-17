"""RPS tournament subsystem — pure-rules + future domain modules (S4.4).

See ``docs/architecture.md`` §"Subsystem decomposition" for the layout
convention.  Modules in this package are pure-ish: they do not own
cog state and do not perform Discord-API I/O.

Modules:
    rules  — move alias map, game-mode whitelist, win-condition table,
             ``normalize_move``, ``determine_winner``
             (consumed by the cog's on_message + handle_bot_match_move +
              resolve_match paths)
"""
