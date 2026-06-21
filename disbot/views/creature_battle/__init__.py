"""Creature PvP battle views (creature-game v1).

The Discord surface for the level-normalized creature PvP flow: a challenge
accept/decline view (:mod:`views.creature_battle.challenge`) and the
battle-outcome embed renderer (:mod:`views.creature_battle.render`). The combat
math lives in :mod:`utils.creatures.battle`; the read boundary that loads each
player's team lives in :mod:`services.creature_battle_service`.
"""

from __future__ import annotations

from views.creature_battle.challenge import CreatureBattleChallengeView
from views.creature_battle.render import build_result_embed

__all__ = [
    "CreatureBattleChallengeView",
    "build_result_embed",
]
