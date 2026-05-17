"""views.xp — XP hub, rank, and config panels + admin modals.

Extracted from ``cogs/xp_cog.py`` during S4.2-followup.  No
PersistentView lives in this package (XP has no restart-safe anchored
panel today) — all views here are ephemeral, timeout-based.

Modules:
    main_panel   — ``_XpHubView`` (HubView, opened by !xpmenu)
    rank_view    — ``_RankView`` / ``_RankSelect`` (!rank dropdown)
    config_panel — ``XpConfigView`` (!xpconfig, admin)
    modals       — 5 admin modals (give/reset/range/cooldown/channel)
"""

from __future__ import annotations

from views.xp.config_panel import XpConfigView
from views.xp.main_panel import _XpHubView
from views.xp.modals import (
    _GiveXpModal,
    _ResetXpModal,
    _XpChannelModal,
    _XpCooldownModal,
    _XpRangeModal,
)
from views.xp.rank_view import _RankSelect, _RankView

__all__ = [
    "XpConfigView",
    "_GiveXpModal",
    "_RankSelect",
    "_RankView",
    "_ResetXpModal",
    "_XpChannelModal",
    "_XpCooldownModal",
    "_XpHubView",
    "_XpRangeModal",
]
