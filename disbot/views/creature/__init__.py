"""Creature game views — the interactive Games-hub panel (completion cert, Q-0209).

The Creatures surface gained an interactive :class:`HubView` panel (the catch /
dex-browser / challenge / ladder hub) in the completion-first deepening run, closing
the certificate's headline rubric-B gap (hub-less v1 → a playable Games-hub surface).
The PvP challenge/rematch/render views live in the sibling
:mod:`views.creature_battle` package.
"""

from __future__ import annotations

from views.creature.embeds import (
    build_battletop_embed,
    build_catch_result_embed,
    build_collectors_embed,
    build_dex_embed,
    build_menu_embed,
    build_record_embed,
    build_rules_embed,
)
from views.creature.menu import (
    CreatureChallengeSelectView,
    CreatureDexView,
    CreatureMenuView,
    open_creature_menu,
)

__all__ = [
    "CreatureChallengeSelectView",
    "CreatureDexView",
    "CreatureMenuView",
    "build_battletop_embed",
    "build_catch_result_embed",
    "build_collectors_embed",
    "build_dex_embed",
    "build_menu_embed",
    "build_record_embed",
    "build_rules_embed",
    "open_creature_menu",
]
