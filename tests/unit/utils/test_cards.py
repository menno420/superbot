"""Tests for the shared card primitives (utils/cards)."""

from __future__ import annotations

import random

import pytest

from utils.cards import RANK_NAMES, Card, Suit, card, make_deck, parse_card


def test_make_deck_is_52_unique() -> None:
    deck = make_deck(shuffle=False)
    assert len(deck) == 52
    assert len(set(deck)) == 52


def test_make_deck_seeded_is_reproducible() -> None:
    a = make_deck(rng=random.Random(7))
    b = make_deck(rng=random.Random(7))
    assert a == b


def test_make_deck_unshuffled_is_ordered() -> None:
    deck = make_deck(shuffle=False)
    # First card is the lowest spade (2♠) by construction order.
    assert deck[0] == Card(rank=2, suit=Suit.SPADES)


def test_card_sorts_by_rank() -> None:
    assert Card(rank=2, suit=Suit.SPADES) < Card(rank=14, suit=Suit.CLUBS)
    hand = [Card(rank=14, suit=Suit.SPADES), Card(rank=3, suit=Suit.HEARTS)]
    assert sorted(hand)[0].rank == 3


def test_str_and_code() -> None:
    assert str(Card(rank=14, suit=Suit.SPADES)) == "A♠"
    assert Card(rank=10, suit=Suit.HEARTS).code == "10H"
    assert RANK_NAMES[11] == "J"


@pytest.mark.parametrize(
    ("code", "rank", "suit"),
    [
        ("AS", 14, Suit.SPADES),
        ("KH", 13, Suit.HEARTS),
        ("10D", 10, Suit.DIAMONDS),
        ("TD", 10, Suit.DIAMONDS),
        ("2c", 2, Suit.CLUBS),
    ],
)
def test_parse_card(code: str, rank: int, suit: Suit) -> None:
    parsed = parse_card(code)
    assert parsed.rank == rank
    assert parsed.suit == suit
    assert card(code) == parsed


def test_parse_card_rejects_garbage() -> None:
    with pytest.raises(ValueError):
        parse_card("ZZ")
    with pytest.raises(ValueError):
        parse_card("A")


def test_card_rejects_bad_rank() -> None:
    with pytest.raises(ValueError):
        Card(rank=1, suit=Suit.SPADES)
