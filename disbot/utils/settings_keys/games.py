"""Settings keys shared by game subsystems.

``ACTIVE_TOURNAMENT`` is written by both ``rps_tournament_cog`` and
``blackjack_cog``; that shared-write is intentional and documented in
the platform blueprint (§8).
"""

ACTIVE_TOURNAMENT = "active_tournament"
