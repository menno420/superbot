"""Poker hand evaluation — pure, deterministic, Discord-free.

Scores a 5-card poker hand into a totally-ordered, comparable value and finds
the best 5-card hand out of 5, 6, or 7 cards (so it serves both 5-card draw and
Texas Hold'em's 7-card showdown).

Correctness over cleverness: :func:`best_hand` brute-forces all
``C(n, 5)`` 5-card combinations and takes the max.  For 7 cards that is 21
combinations — trivial, and obviously correct (no bit-twiddling lookup tables to
get subtly wrong).

The score is a tuple ``(category, *tiebreakers)`` where bigger is better, so two
hands compare with plain ``<``/``>``/``==``.  This makes ties (identical score)
detectable for split pots.

Public API
----------
- :class:`HandCategory` — the nine ranking categories.
- :func:`score_five` — score exactly five cards → :class:`HandRank`.
- :func:`best_hand` — best 5-of-n → :class:`HandRank`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from itertools import combinations

from utils.cards import Card

__all__ = ["HandCategory", "HandRank", "best_hand", "score_five"]


class HandCategory(IntEnum):
    """Poker hand categories, ordered weakest → strongest."""

    HIGH_CARD = 0
    PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8

    @property
    def label(self) -> str:
        return {
            HandCategory.HIGH_CARD: "High Card",
            HandCategory.PAIR: "Pair",
            HandCategory.TWO_PAIR: "Two Pair",
            HandCategory.THREE_OF_A_KIND: "Three of a Kind",
            HandCategory.STRAIGHT: "Straight",
            HandCategory.FLUSH: "Flush",
            HandCategory.FULL_HOUSE: "Full House",
            HandCategory.FOUR_OF_A_KIND: "Four of a Kind",
            HandCategory.STRAIGHT_FLUSH: "Straight Flush",
        }[self]


@dataclass(frozen=True, order=True)
class HandRank:
    """A comparable poker hand score.

    ``key`` is ``(category_value, tiebreak_ranks...)`` and is the only field
    used for ordering, so ``HandRank`` objects compare directly and equal keys
    mean a genuine tie (split pot).  ``category`` and ``cards`` ride along for
    display only.
    """

    key: tuple[int, ...]
    category: HandCategory
    cards: tuple[Card, ...]

    @property
    def label(self) -> str:
        return self.category.label


def _straight_high(ranks: list[int]) -> int | None:
    """Return the high card of a straight in *ranks* (distinct, desc), else None.

    Handles the ace-low "wheel" (A-2-3-4-5), where the ace plays low and the
    straight's high card is the 5.
    """
    distinct = sorted(set(ranks), reverse=True)
    # Ace-low wheel: treat ace (14) as 1 as well.
    distinct_with_low = distinct + [1] if 14 in distinct else distinct
    run = 1
    for i in range(1, len(distinct_with_low)):
        if distinct_with_low[i] == distinct_with_low[i - 1] - 1:
            run += 1
            if run >= 5:
                return distinct_with_low[i - 4]
        else:
            run = 1
    return None


def score_five(cards: list[Card]) -> HandRank:
    """Score exactly five cards into a comparable :class:`HandRank`."""
    if len(cards) != 5:
        raise ValueError(f"score_five needs exactly 5 cards, got {len(cards)}")

    ranks = sorted((c.rank for c in cards), reverse=True)
    is_flush = len({c.suit for c in cards}) == 1
    straight_high = _straight_high(ranks)

    # Group ranks by count, ordered by (count desc, rank desc) — so the most
    # frequent rank leads, ties broken by rank.  This ordering is exactly the
    # tiebreak order for pairs/trips/quads/full-house/two-pair.
    counts: dict[int, int] = {}
    for r in ranks:
        counts[r] = counts.get(r, 0) + 1
    by_count = sorted(counts.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    count_shape = tuple(c for _, c in by_count)
    ordered_ranks = tuple(r for r, _ in by_count)
    tuple_cards = tuple(sorted(cards, reverse=True))

    if straight_high is not None and is_flush:
        return HandRank(
            key=(HandCategory.STRAIGHT_FLUSH, straight_high),
            category=HandCategory.STRAIGHT_FLUSH,
            cards=tuple_cards,
        )
    if count_shape == (4, 1):
        return HandRank(
            key=(HandCategory.FOUR_OF_A_KIND, *ordered_ranks),
            category=HandCategory.FOUR_OF_A_KIND,
            cards=tuple_cards,
        )
    if count_shape == (3, 2):
        return HandRank(
            key=(HandCategory.FULL_HOUSE, *ordered_ranks),
            category=HandCategory.FULL_HOUSE,
            cards=tuple_cards,
        )
    if is_flush:
        return HandRank(
            key=(HandCategory.FLUSH, *ranks),
            category=HandCategory.FLUSH,
            cards=tuple_cards,
        )
    if straight_high is not None:
        return HandRank(
            key=(HandCategory.STRAIGHT, straight_high),
            category=HandCategory.STRAIGHT,
            cards=tuple_cards,
        )
    if count_shape == (3, 1, 1):
        return HandRank(
            key=(HandCategory.THREE_OF_A_KIND, *ordered_ranks),
            category=HandCategory.THREE_OF_A_KIND,
            cards=tuple_cards,
        )
    if count_shape == (2, 2, 1):
        return HandRank(
            key=(HandCategory.TWO_PAIR, *ordered_ranks),
            category=HandCategory.TWO_PAIR,
            cards=tuple_cards,
        )
    if count_shape == (2, 1, 1, 1):
        return HandRank(
            key=(HandCategory.PAIR, *ordered_ranks),
            category=HandCategory.PAIR,
            cards=tuple_cards,
        )
    return HandRank(
        key=(HandCategory.HIGH_CARD, *ranks),
        category=HandCategory.HIGH_CARD,
        cards=tuple_cards,
    )


def best_hand(cards: list[Card]) -> HandRank:
    """Return the best 5-card :class:`HandRank` from 5, 6, or 7 cards."""
    if len(cards) < 5:
        raise ValueError(f"best_hand needs at least 5 cards, got {len(cards)}")
    if len(cards) == 5:
        return score_five(cards)
    return max(score_five(list(combo)) for combo in combinations(cards, 5))
