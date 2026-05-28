"""Verify the difficulty-cost formula against the published Bomb Shooter table.

Every (Easy, Medium, Hard, Impoppable) tuple below is copied verbatim from
the tower's cost table. The formula stores only the Medium value and must
reproduce the other three exactly — this test is the proof, and a guard
against anyone tweaking the multipliers or rounding.
"""

from __future__ import annotations

import pytest

from utils.btd6.difficulty_costs import (
    all_difficulty_costs,
    cost_for_difficulty,
    normalize_difficulty,
)

# (easy, medium, hard, impoppable) for every Bomb Shooter upgrade + Paragon.
BOMB_SHOOTER_COSTS: tuple[tuple[int, int, int, int], ...] = (
    # Path 1
    (210, 250, 270, 300),
    (550, 650, 700, 780),
    (935, 1100, 1190, 1320),
    (2380, 2800, 3025, 3360),
    (46750, 55000, 59400, 66000),
    # Path 2
    (210, 250, 270, 300),
    (340, 400, 430, 480),
    (850, 1000, 1080, 1200),
    (2930, 3450, 3725, 4140),
    (22100, 26000, 28080, 31200),
    # Path 3
    (170, 200, 215, 240),
    (255, 300, 325, 360),
    (595, 700, 755, 840),
    (2125, 2500, 2700, 3000),
    (25500, 30000, 32400, 36000),
    # Paragon
    (510000, 600000, 648000, 720000),
)


@pytest.mark.parametrize(("easy", "medium", "hard", "impoppable"), BOMB_SHOOTER_COSTS)
def test_formula_reproduces_published_table(easy, medium, hard, impoppable):
    assert all_difficulty_costs(medium) == {
        "easy": easy,
        "medium": medium,
        "hard": hard,
        "impoppable": impoppable,
    }


def test_medium_is_identity():
    assert cost_for_difficulty(1234, "medium") == 1234


def test_half_tie_rounds_down():
    # 250 × 0.85 = 212.5 → 210 (tie resolves to the lower multiple of 5).
    assert cost_for_difficulty(250, "easy") == 210


def test_case_and_alias_handling():
    assert cost_for_difficulty(1000, "EASY") == cost_for_difficulty(1000, "easy")
    # CHIMPS prices like Hard.
    assert cost_for_difficulty(1000, "chimps") == cost_for_difficulty(1000, "hard")
    assert normalize_difficulty("  Normal ") == "medium"


def test_unknown_difficulty_raises():
    with pytest.raises(ValueError):
        cost_for_difficulty(1000, "nightmare")
