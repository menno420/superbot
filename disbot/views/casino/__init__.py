"""Casino subsystem views — group casino games under the Games hub.

The marquee mechanic lives in :mod:`views.casino.poker_table`: a multiplayer
table where every seated player gets their own **auto-updating ephemeral**
message, so a group plays one table at once.  :mod:`views.casino.hub` is the
navigation panel that launches it.
"""

from __future__ import annotations

from views.casino.hub import (
    CasinoHubView,
    build_casino_hub_embed,
    build_casino_hub_panel,
)

__all__ = [
    "CasinoHubView",
    "build_casino_hub_embed",
    "build_casino_hub_panel",
]
