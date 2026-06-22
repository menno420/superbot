"""Tests for the Texas Hold'em engine (utils/poker/engine)."""

from __future__ import annotations

import random

import pytest

from utils.cards import card
from utils.poker.engine import Action, Player, PokerError, PokerGame, Stage


def make_players(n: int, stack: int = 100) -> list[Player]:
    return [Player(user_id=i + 1, name=f"P{i + 1}", stack=stack) for i in range(n)]


def fresh_game(n: int = 3, stack: int = 100) -> PokerGame:
    g = PokerGame(
        make_players(n, stack),
        small_blind=1,
        big_blind=2,
        button=0,
        rng=random.Random(1234),
    )
    g.begin_hand()
    return g


# ---------------------------------------------------------------- setup / blinds


def test_blinds_and_first_actor_three_handed() -> None:
    g = fresh_game(3)
    # Non heads-up: SB = seat 1, BB = seat 2, first to act = button (seat 0).
    assert g.players[1].committed_round == 1
    assert g.players[2].committed_round == 2
    assert g.current == 0
    assert g.current_bet == 2
    assert g.stage == Stage.PREFLOP
    assert all(len(p.hole) == 2 for p in g.players)


def test_heads_up_button_is_small_blind() -> None:
    g = PokerGame(make_players(2), small_blind=1, big_blind=2, button=0)
    g.begin_hand()
    # Heads-up: button (seat 0) posts SB and acts first preflop.
    assert g.players[0].committed_round == 1
    assert g.players[1].committed_round == 2
    assert g.current == 0


def test_needs_two_funded_players() -> None:
    g = PokerGame(make_players(2), button=0)
    g.players[1].stack = 0
    with pytest.raises(PokerError):
        g.begin_hand()


# ------------------------------------------------------------------- betting


def test_preflop_round_completes_with_bb_option() -> None:
    g = fresh_game(3)
    assert g.current == 0
    g.act(Action.CALL)  # button calls 2
    assert g.current == 1
    g.act(Action.CALL)  # SB completes
    assert g.current == 2  # BB gets the option
    g.act(Action.CHECK)  # BB checks → round over
    assert g.stage == Stage.FLOP
    assert g.pot_total == 6
    assert len(g.board) == 3
    # Postflop first actor is the first live seat left of the button (SB).
    assert g.current == 1


def test_raise_reopens_action() -> None:
    g = fresh_game(3)
    g.act(Action.RAISE, raise_to=6)  # button raises to 6
    assert g.current_bet == 6
    assert g.current == 1
    g.act(Action.CALL)  # SB calls
    g.act(Action.CALL)  # BB calls
    assert g.stage == Stage.FLOP
    assert g.pot_total == 18


def test_min_raise_enforced() -> None:
    g = fresh_game(3)
    with pytest.raises(PokerError):
        g.act(Action.RAISE, raise_to=3)  # below current_bet(2)+min_raise(2)=4


def test_check_facing_bet_rejected() -> None:
    g = fresh_game(3)
    with pytest.raises(PokerError):
        g.act(Action.CHECK)  # button faces the big blind


def test_fold_to_one_player_awards_pot() -> None:
    g = PokerGame(make_players(2), small_blind=1, big_blind=2, button=0)
    g.begin_hand()
    start_bb = g.players[1].stack
    g.act(Action.FOLD)  # button/SB folds preflop
    assert g.is_hand_over
    assert g.stage == Stage.COMPLETE
    assert len(g.results) == 1
    assert g.results[0].user_id == g.players[1].user_id
    assert g.results[0].amount == 3  # SB(1) + BB(2)
    assert g.results[0].hand_label is None
    assert g.players[1].stack == start_bb + 3


def test_full_hand_reaches_showdown() -> None:
    g = fresh_game(2, stack=100)
    # Heads-up: button(0)=SB acts first. Just call/check everything down.
    guard = 0
    while not g.is_hand_over and guard < 40:
        guard += 1
        actions = g.legal_actions()
        if "check" in actions:
            g.act(Action.CHECK)
        elif "call" in actions:
            g.act(Action.CALL)
        else:
            g.act(Action.FOLD)
    assert g.is_hand_over
    assert len(g.board) == 5
    # The whole pot is awarded back out — chips are conserved.
    assert sum(p.stack for p in g.players) == 200


def test_chips_conserved_across_betting() -> None:
    g = fresh_game(3, stack=100)
    total_before = sum(p.stack for p in g.players) + g.pot_total
    g.act(Action.RAISE, raise_to=10)
    g.act(Action.CALL)
    g.act(Action.CALL)
    total_after = sum(p.stack for p in g.players) + g.pot_total
    assert total_before == total_after == 300


# ------------------------------------------------------------------- side pots


def _settle_with(
    contributions: list[int],
    holes: list[tuple[str, str]],
    board: list[str],
    folded: list[bool] | None = None,
) -> PokerGame:
    n = len(contributions)
    g = PokerGame(make_players(n, stack=0), button=0)
    for i, p in enumerate(g.players):
        p.committed_hand = contributions[i]
        p.hole = [card(holes[i][0]), card(holes[i][1])]
        p.folded = folded[i] if folded else False
    g.board = [card(c) for c in board]
    g._settle_showdown()
    return g


def test_side_pot_short_all_in_loses_side() -> None:
    # A all-in for 50 (best hand), B & C each 100. A wins the 150 main pot only;
    # B (better than C) takes the 100 side pot.
    g = _settle_with(
        contributions=[50, 100, 100],
        holes=[("AH", "AD"), ("KH", "KS"), ("3H", "4D")],
        board=["2C", "7D", "9S", "JH", "QD"],
    )
    assert g.players[0].stack == 150  # main pot
    assert g.players[1].stack == 100  # side pot
    assert g.players[2].stack == 0


def test_split_pot_even() -> None:
    # Both players play the board (identical hands) → pot splits evenly.
    g = _settle_with(
        contributions=[50, 50],
        holes=[("2H", "3D"), ("2S", "3C")],
        board=["10C", "JD", "QS", "KH", "AD"],
    )
    assert g.players[0].stack == 50
    assert g.players[1].stack == 50


def test_folded_player_chips_stay_in_pot() -> None:
    # C folded but contributed 20; that dead money is still won by the best hand.
    g = _settle_with(
        contributions=[100, 100, 20],
        holes=[("AH", "AD"), ("KH", "KS"), ("3H", "4D")],
        board=["2C", "7D", "9S", "JH", "QD"],
        folded=[False, False, True],
    )
    assert g.players[0].stack == 220  # 100 + 100 + 20 dead money
    assert g.players[1].stack == 0
