"""Shared RPS constants + PvP pending-match registry.

Pulled out of cogs/rps_tournament_cog.py during D4 so the view
classes can be hosted in :mod:`views.rps.*` without circular imports
back into the cog.
"""

from __future__ import annotations

# Win matrix: key beats value.
_RPS_WINS: dict[str, str] = {
    "rock": "scissors",
    "scissors": "paper",
    "paper": "rock",
}

# Display emoji per move.
_RPS_EMOJI: dict[str, str] = {
    "rock": "🪨",
    "paper": "📄",
    "scissors": "✂️",
}

# Coins awarded for a free-play (no-bet) win.
_FREE_WIN: int = 30

# Pending PvP matches keyed by frozenset({p1_id, p2_id}).
# Value shape: {"choices": dict[int, str], "guild_id": int, "bet": int,
#               "channel_id": int}.
_rps_pvp_pending: dict[frozenset, dict] = {}

# PR G1 — game_state checkpoint subsystem string and payload version.
# Single row per match, keyed at the canonical (smallest) player id so
# the natural game_state UNIQUE constraint is honoured.  Bumping the
# version forces ``cog_load`` to drop incompatible payloads instead of
# trying to resume them with the wrong shape.
RPS_PVP_PENDING_SUBSYSTEM = "rps_pvp_pending"
RPS_PVP_PENDING_VERSION = 1


def rps_pvp_canonical_user_id(p1_id: int, p2_id: int) -> int:
    """The user_id used as the natural key for an rps_pvp_pending row.

    Either player's id would do; we pick the smaller of the two so two
    different views (one held by each player) write the same row and
    cooperate via the upsert.
    """
    return min(p1_id, p2_id)
