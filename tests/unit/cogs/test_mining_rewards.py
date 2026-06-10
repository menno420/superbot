"""Tests for utils.mining.rewards — extracted pure functions (S4.1).

These were inline inside the pre-decomposition ``cogs/mining_cog.py``
listener and were untestable without a Discord mock harness.  After
S4.1 they live in their own module and can be exercised directly.
"""

from __future__ import annotations

import random

import pytest

from utils.mining import rewards


@pytest.fixture(autouse=True)
def _deterministic():
    """Seed Python's random so test assertions are stable."""
    random.seed(42)
    yield


# ---------------------------------------------------------------------------
# roll_mine_loot
# ---------------------------------------------------------------------------


def test_roll_mine_loot_returns_known_ore_name():
    found, amount = rewards.roll_mine_loot(has_pickaxe=False)
    assert found in rewards.ORE_WEIGHTS
    assert 1 <= amount <= 3


def test_roll_mine_loot_pickaxe_doubles_amount():
    """With the same RNG seed, pickaxe path yields exactly 2× the no-pickaxe path."""
    random.seed(1)
    _, no_pickaxe = rewards.roll_mine_loot(has_pickaxe=False)
    random.seed(1)
    _, with_pickaxe = rewards.roll_mine_loot(has_pickaxe=True)
    assert with_pickaxe == no_pickaxe * 2


def test_ore_weights_contain_all_four_resources():
    assert set(rewards.ORE_WEIGHTS) == {"stone", "iron", "gold", "diamond"}


def test_ore_weights_for_depth_zero_equals_surface_table():
    # Depth 0 must be byte-identical to the legacy table so surface behaviour
    # (and the pickaxe-doubling test above) is unchanged.
    assert rewards.ore_weights_for_depth(0) == rewards.ORE_WEIGHTS


def test_deeper_bands_favor_rarer_ore():
    surface = rewards.ore_weights_for_depth(0)
    deep = rewards.ore_weights_for_depth(2)
    assert deep["stone"] < surface["stone"]  # stone gets rarer with depth
    assert deep["diamond"] > surface["diamond"]  # rare ore gets likelier
    assert deep["gold"] > surface["gold"]
    # Same four ores at every depth — callers never see an unknown drop.
    assert set(deep) == set(rewards.ORE_WEIGHTS)


def test_roll_mine_loot_keeps_known_ore_names_at_every_depth():
    for depth in range(4):
        found, amount = rewards.roll_mine_loot(has_pickaxe=False, depth=depth)
        assert found in rewards.ORE_WEIGHTS
        assert 1 <= amount <= 3


# ---------------------------------------------------------------------------
# roll_harvest_amount
# ---------------------------------------------------------------------------


def test_roll_harvest_amount_no_axe_is_1_to_3():
    for _ in range(50):
        amount = rewards.roll_harvest_amount(has_axe=False)
        assert 1 <= amount <= 3


def test_roll_harvest_amount_with_axe_doubles_no_axe():
    random.seed(1)
    no_axe = rewards.roll_harvest_amount(has_axe=False)
    random.seed(1)
    with_axe = rewards.roll_harvest_amount(has_axe=True)
    assert with_axe == no_axe * 2


# ---------------------------------------------------------------------------
# roll_explore_outcome
# ---------------------------------------------------------------------------


def test_roll_explore_outcome_returns_a_known_tuple():
    text, item, amount = rewards.roll_explore_outcome()
    assert (text, item, amount) in rewards.EXPLORE_OUTCOMES


def test_explore_outcomes_have_expected_shape():
    """Every outcome tuple is (str, str|None, int)."""
    for text, item, amount in rewards.EXPLORE_OUTCOMES:
        assert isinstance(text, str)
        assert item is None or isinstance(item, str)
        assert isinstance(amount, int)
