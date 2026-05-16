"""Pure blackjack card / hand / deck primitives.

Extracted from cogs/blackjack_cog.py during P3 PR-14.  Hosting these
in services/ instead of the cog means the payout math is testable
without a Discord client mock, and three call surfaces
(single-player, PvP, tournament) share the same canonical
implementation rather than copy-pasting card logic.

The functions are deterministic for everything except :func:`new_deck`,
which uses ``random.shuffle`` and is documented as the only side
effect.  Pass a pre-shuffled deck to keep tests reproducible.

Public API
----------
- :data:`SUITS`, :data:`RANKS` — card alphabets.
- :func:`rank_value(rank)` → int — face-value table (A = 11).
- :func:`hand_value(hand)` → int — total with the standard
  ace-soft-to-hard demotion rule (Aces drop from 11 → 1 if needed
  to keep the hand under 22).
- :func:`new_deck()` → list[str] — shuffled 52-card deck.
- :func:`hand_str(hand, hide_second=False)` → str — display string.
  ``hide_second=True`` masks the dealer's hole card.
- :func:`is_blackjack(hand)` → bool — natural 21 (exactly two
  cards summing to 21).

Cards are strings of the form ``"<rank> <suit>"``, e.g. ``"A ♠"``.
"""

from __future__ import annotations

import random

SUITS: tuple[str, ...] = ("♠", "♥", "♦", "♣")
RANKS: tuple[str, ...] = (
    "A",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "J",
    "Q",
    "K",
)


def rank_value(rank: str) -> int:
    """Face value for a single rank string.  Aces are 11 by default."""
    if rank in ("J", "Q", "K"):
        return 10
    if rank == "A":
        return 11
    return int(rank)


def hand_value(hand: list[str]) -> int:
    """Total a hand, demoting aces from 11 → 1 to stay under 22 when possible."""
    total = sum(rank_value(c.split()[0]) for c in hand)
    aces = sum(1 for c in hand if c.startswith("A"))
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def new_deck() -> list[str]:
    """Return a fresh shuffled deck.  The only function with side effects."""
    deck = [f"{r} {s}" for r in RANKS for s in SUITS]
    random.shuffle(deck)
    return deck


def hand_str(hand: list[str], hide_second: bool = False) -> str:
    """Display a hand; mask the second card when *hide_second* is true."""
    if hide_second:
        return f"{hand[0]}  ||?||"
    return "  ".join(hand)


def is_blackjack(hand: list[str]) -> bool:
    """True iff *hand* is a natural blackjack (two cards totalling 21)."""
    return len(hand) == 2 and hand_value(hand) == 21
