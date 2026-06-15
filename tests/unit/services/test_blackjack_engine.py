"""Tests for services.blackjack_engine (P3 PR-14).

Pure-logic tests with zero Discord mocking — exactly what the
decomposition was meant to enable.
"""

from __future__ import annotations

import pytest

from services import blackjack_engine as eng

# ---------------------------------------------------------------------------
# rank_value
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "rank, expected",
    [
        ("A", 11),
        ("2", 2),
        ("9", 9),
        ("10", 10),
        ("J", 10),
        ("Q", 10),
        ("K", 10),
    ],
)
def test_rank_value(rank: str, expected: int):
    assert eng.rank_value(rank) == expected


# ---------------------------------------------------------------------------
# hand_value — including the ace soft/hard demotion rule
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "hand, expected",
    [
        # Simple totals
        (["5 ♠", "7 ♥"], 12),
        (["10 ♦", "K ♣"], 20),
        # Natural blackjack
        (["A ♠", "K ♣"], 21),
        # Soft hand stays soft when under 22
        (["A ♠", "5 ♥"], 16),
        # Soft → hard demotion when over 21
        (["A ♠", "9 ♥", "5 ♦"], 15),  # 11+9+5=25 → demote A: 1+9+5=15
        # Multiple aces, multi-step demotion
        (["A ♠", "A ♥", "9 ♦"], 21),  # 11+1+9 = 21
        (["A ♠", "A ♥", "K ♦"], 12),  # 11+1+10 → demote first: 1+1+10
        (["A ♠", "A ♥", "A ♦", "A ♣"], 14),  # 11+1+1+1
        # Hard bust
        (["10 ♠", "K ♥", "5 ♦"], 25),
    ],
)
def test_hand_value(hand: list[str], expected: int):
    assert eng.hand_value(hand) == expected


# ---------------------------------------------------------------------------
# is_blackjack
# ---------------------------------------------------------------------------


def test_is_blackjack_natural_21():
    assert eng.is_blackjack(["A ♠", "K ♥"])
    assert eng.is_blackjack(["A ♠", "10 ♦"])
    assert eng.is_blackjack(["Q ♣", "A ♥"])


def test_is_blackjack_rejects_three_card_21():
    """21 reached with 3+ cards is not a natural blackjack."""
    assert not eng.is_blackjack(["7 ♠", "7 ♥", "7 ♦"])
    assert not eng.is_blackjack(["A ♠", "5 ♥", "5 ♦"])


def test_is_blackjack_rejects_non_21_hands():
    assert not eng.is_blackjack(["K ♠", "9 ♥"])  # 19
    assert not eng.is_blackjack(["A ♠", "A ♥"])  # 12


# ---------------------------------------------------------------------------
# hand_str
# ---------------------------------------------------------------------------


def test_hand_str_joins_with_spaces():
    assert eng.hand_str(["A ♠", "K ♥"]) == "A ♠  K ♥"


def test_hand_str_hides_second_card():
    """Dealer's hole card masked when hide_second=True."""
    assert eng.hand_str(["A ♠", "K ♥"], hide_second=True) == "A ♠  ||?||"


# ---------------------------------------------------------------------------
# new_deck
# ---------------------------------------------------------------------------


def test_new_deck_returns_52_unique_cards():
    deck = eng.new_deck()
    assert len(deck) == 52
    assert len(set(deck)) == 52


def test_new_deck_uses_all_suit_rank_combinations():
    deck = eng.new_deck()
    expected = {f"{r} {s}" for r in eng.RANKS for s in eng.SUITS}
    assert set(deck) == expected


def test_new_deck_is_shuffled():
    """Two fresh decks should differ at some position (with overwhelming probability)."""
    a = eng.new_deck()
    b = eng.new_deck()
    assert a != b
