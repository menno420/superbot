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
