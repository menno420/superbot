"""Pure poker domain: card evaluation + a Texas Hold'em engine.

Discord-free and deterministic given a deck, so the betting/pot/showdown logic
is unit-tested in isolation and the casino view layer is a thin renderer.
"""

from __future__ import annotations

from utils.poker.engine import (
    Action,
    Player,
    PokerError,
    PokerGame,
    PotResult,
    Stage,
)
from utils.poker.evaluate import HandCategory, HandRank, best_hand, score_five

__all__ = [
    "Action",
    "HandCategory",
    "HandRank",
    "Player",
    "PokerError",
    "PokerGame",
    "PotResult",
    "Stage",
    "best_hand",
    "score_five",
]
