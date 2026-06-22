"""Tests for poker hand evaluation (utils/poker/evaluate)."""

from __future__ import annotations

from utils.cards import card
from utils.poker.evaluate import HandCategory, best_hand, score_five


def cards(*codes: str) -> list:
    return [card(c) for c in codes]


def test_category_detection() -> None:
    cases = {
        HandCategory.STRAIGHT_FLUSH: cards("10H", "JH", "QH", "KH", "AH"),
        HandCategory.FOUR_OF_A_KIND: cards("9H", "9D", "9S", "9C", "KH"),
        HandCategory.FULL_HOUSE: cards("9H", "9D", "9S", "KC", "KH"),
        HandCategory.FLUSH: cards("2H", "5H", "9H", "JH", "KH"),
        HandCategory.STRAIGHT: cards("5H", "6D", "7S", "8C", "9H"),
        HandCategory.THREE_OF_A_KIND: cards("9H", "9D", "9S", "2C", "KH"),
        HandCategory.TWO_PAIR: cards("9H", "9D", "KS", "KC", "2H"),
        HandCategory.PAIR: cards("9H", "9D", "2S", "5C", "KH"),
        HandCategory.HIGH_CARD: cards("2H", "5D", "9S", "JC", "KH"),
    }
    for expected, hand in cases.items():
        assert score_five(hand).category == expected, expected


def test_wheel_straight_is_five_high() -> None:
    wheel = score_five(cards("AH", "2D", "3S", "4C", "5H"))
    assert wheel.category == HandCategory.STRAIGHT
    higher = score_five(cards("2H", "3D", "4S", "5C", "6H"))
    assert higher > wheel  # 6-high straight beats the wheel


def test_ace_high_straight_beats_king_high() -> None:
    broadway = score_five(cards("10H", "JD", "QS", "KC", "AH"))
    king = score_five(cards("9H", "10D", "JS", "QC", "KH"))
    assert broadway > king


def test_flush_beats_straight() -> None:
    flush = score_five(cards("2H", "5H", "9H", "JH", "KH"))
    straight = score_five(cards("5H", "6D", "7S", "8C", "9H"))
    assert flush > straight


def test_kicker_breaks_pair_tie() -> None:
    pair_ace_kicker = score_five(cards("9H", "9D", "AS", "5C", "2H"))
    pair_king_kicker = score_five(cards("9S", "9C", "KS", "5D", "2D"))
    assert pair_ace_kicker > pair_king_kicker


def test_identical_hands_tie() -> None:
    a = score_five(cards("9H", "9D", "AS", "5C", "2H"))
    b = score_five(cards("9S", "9C", "AH", "5D", "2D"))
    assert a.key == b.key


def test_best_hand_picks_best_five_of_seven() -> None:
    # Seven cards containing a flush; best_hand must find it.
    hand = best_hand(cards("AH", "KH", "QH", "2H", "9H", "3S", "4D"))
    assert hand.category == HandCategory.FLUSH
    # Seven cards making a full house out of two pair + a third.
    fh = best_hand(cards("KH", "KD", "KS", "2C", "2H", "5D", "9S"))
    assert fh.category == HandCategory.FULL_HOUSE


def test_best_hand_seven_card_straight() -> None:
    hand = best_hand(cards("3H", "4D", "5S", "6C", "7H", "KD", "AS"))
    assert hand.category == HandCategory.STRAIGHT
