"""Settings keys shared by game subsystems.

``ACTIVE_TOURNAMENT`` is written by both ``rps_tournament_cog`` and
``blackjack_cog``; that shared-write is intentional and documented in
the platform blueprint (§8).

PR 8 adds per-subsystem default-config keys. Each is read by the
runtime command body when the operator does not supply an explicit
value (plan §2.12 hard rule: only add settings the runtime reads).
"""

ACTIVE_TOURNAMENT = "active_tournament"

# RPS — default entry fee applied when ``!rpsregister`` is invoked
# without an explicit ``entry_fee`` argument.
RPS_DEFAULT_ENTRY_FEE = "rps_default_entry_fee"

# Blackjack — default entry fee applied when ``!bjtournament`` is
# invoked without an explicit ``entry_fee`` argument.
BLACKJACK_DEFAULT_ENTRY_FEE = "blackjack_default_entry_fee"

# Deathmatch — per-turn timeout (seconds) the ``_DuelView`` uses when
# a duel is accepted from the panel. Falls back to 60 (the historical
# in-code default) when unset.
DEATHMATCH_TURN_TIMEOUT = "deathmatch_turn_timeout"
