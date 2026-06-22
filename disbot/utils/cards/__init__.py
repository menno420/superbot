"""Reusable standard-52-card-deck primitives (pure, Discord-free).

Blackjack ships its own card helpers in ``services/blackjack_engine.py``, but
those are blackjack-specific: cards are bare ``"<rank> <suit>"`` strings and the
only "value" is the blackjack face value (A=11, demote on bust).  Poker — and
any future casino game that needs to *rank and compare* cards — needs a real,
ordered card model: an ace that sorts high (or low in a wheel straight), suits
that matter for flushes, and value-comparable cards.

This module is that shared model.  It is intentionally pure: stdlib only, no
Discord, fully deterministic except :func:`make_deck` (which shuffles).  Pass a
pre-built deck to keep tests reproducible.

Public API
----------
- :class:`Suit` — the four suits with their glyphs.
- :class:`Card` — a frozen ``(rank, suit)`` value object; ``rank`` is an int
  2..14 (J=11, Q=12, K=13, A=14) so cards compare and sort by strength.
- :data:`RANKS`, :data:`SUITS` — the alphabets.
- :func:`make_deck` — a fresh 52-card deck (shuffled unless ``shuffle=False``).
- :func:`card` / :func:`parse_card` — build a card from a short code (``"AS"``,
  ``"10H"``, ``"TD"``).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from functools import total_ordering

__all__ = [
    "RANKS",
    "RANK_NAMES",
    "SUITS",
    "Card",
    "Suit",
    "card",
    "make_deck",
    "parse_card",
]


@total_ordering
class Suit(Enum):
    """The four French-deck suits, value = the display glyph.

    Totally ordered by declaration order so a ``(rank, suit)`` card is sortable
    — suits never *rank* a poker hand (flushes are detected by sameness), the
    order just makes a sorted hand deterministic for display.
    """

    SPADES = "♠"
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"

    def __lt__(self, other: object) -> bool:
        if self.__class__ is not other.__class__:
            return NotImplemented
        members = list(Suit)
        return members.index(self) < members.index(other)  # type: ignore[arg-type]

    @property
    def letter(self) -> str:
        """The single-letter code (S/H/D/C) used by :func:`parse_card`."""
        return self.name[0]

    @classmethod
    def from_letter(cls, letter: str) -> Suit:
        for suit in cls:
            if suit.letter == letter.upper():
                return suit
        raise ValueError(f"unknown suit letter: {letter!r}")


# Rank ints, ace high.  2..10 are their face value; J=11, Q=12, K=13, A=14.
RANKS: tuple[int, ...] = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14)
SUITS: tuple[Suit, ...] = (Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS)

# rank int → short display char (the code used in card strings / parsing).
RANK_NAMES: dict[int, str] = {
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7",
    8: "8",
    9: "9",
    10: "10",
    11: "J",
    12: "Q",
    13: "K",
    14: "A",
}
_NAME_TO_RANK: dict[str, int] = {name: rank for rank, name in RANK_NAMES.items()}
# "T" is the common single-char alias for ten in card codes.
_NAME_TO_RANK["T"] = 10


@dataclass(frozen=True, order=True)
class Card:
    """A single playing card.

    ``rank`` (2..14) leads the field order so cards sort by strength; ``suit``
    is the tiebreak only so a sorted hand is deterministic (suits never rank a
    poker hand — flushes are detected by *sameness*, not suit order).
    """

    rank: int
    suit: Suit

    def __post_init__(self) -> None:
        if self.rank not in RANK_NAMES:
            raise ValueError(f"rank must be 2..14, got {self.rank!r}")

    @property
    def rank_name(self) -> str:
        return RANK_NAMES[self.rank]

    def __str__(self) -> str:
        return f"{self.rank_name}{self.suit.value}"

    @property
    def code(self) -> str:
        """The parse-able short code, e.g. ``"AS"``, ``"10H"``."""
        return f"{self.rank_name}{self.suit.letter}"


def card(code: str) -> Card:
    """Build a :class:`Card` from a short code: ``"AS"``, ``"10H"``, ``"TD"``."""
    return parse_card(code)


def parse_card(code: str) -> Card:
    """Parse a card code (``"AS"``, ``"KH"``, ``"10D"``, ``"TD"``) → :class:`Card`."""
    code = code.strip()
    if len(code) < 2:
        raise ValueError(f"card code too short: {code!r}")
    rank_part, suit_part = code[:-1], code[-1]
    rank = _NAME_TO_RANK.get(rank_part.upper())
    if rank is None:
        raise ValueError(f"unknown rank in card code: {code!r}")
    return Card(rank=rank, suit=Suit.from_letter(suit_part))


def make_deck(*, shuffle: bool = True, rng: random.Random | None = None) -> list[Card]:
    """Return a fresh 52-card deck.

    Shuffled by default (the only nondeterminism).  Pass ``shuffle=False`` for a
    deterministic ordered deck, or a seeded ``rng`` for reproducible shuffles in
    tests / simulations.
    """
    deck = [Card(rank=r, suit=s) for s in SUITS for r in RANKS]
    if shuffle:
        (rng or random).shuffle(deck)
    return deck
