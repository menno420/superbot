"""Tests for utils.xp_migration (pure parsing) + the level-math inverse."""

from __future__ import annotations

import pytest

from utils import xp_migration as xpm
from utils.db.xp import level_progress, total_xp_for_level, xp_for_level


# --------------------------------------------------------------------------- #
# level math — total_xp_for_level is the exact inverse of level_progress
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("level", list(range(0, 40)))
def test_total_xp_for_level_round_trips(level: int):
    total = total_xp_for_level(level)
    lvl, into, need = level_progress(total)
    assert (lvl, into, need) == (level, 0, xp_for_level(level))


def test_total_xp_for_level_one_below_boundary_is_previous_level():
    # Landing one XP short of level L must still read as level L-1.
    for level in range(1, 25):
        lvl, _, _ = level_progress(total_xp_for_level(level) - 1)
        assert lvl == level - 1


def test_total_xp_for_level_zero_and_negative_are_zero():
    assert total_xp_for_level(0) == 0
    assert total_xp_for_level(-3) == 0


def test_total_xp_for_level_is_monotonic():
    totals = [total_xp_for_level(level) for level in range(0, 30)]
    assert totals == sorted(totals)
    assert len(set(totals)) == len(totals)  # strictly increasing


# --------------------------------------------------------------------------- #
# format registry
# --------------------------------------------------------------------------- #
def test_default_format_is_arcane():
    assert xpm.DEFAULT_FORMAT == "arcane"
    assert xpm.get_format(xpm.DEFAULT_FORMAT) is not None


def test_get_format_is_case_insensitive_and_none_safe():
    assert xpm.get_format("ARCANE").key == "arcane"
    assert xpm.get_format("  MeE6 ").key == "mee6"
    assert xpm.get_format("nope") is None
    assert xpm.get_format(None) is None


def test_format_keys_are_stable_and_cover_known_bots():
    keys = xpm.format_keys()
    assert {"arcane", "mee6", "superbot", "generic"} <= set(keys)


# --------------------------------------------------------------------------- #
# parse_level_message — Arcane (the live case)
# --------------------------------------------------------------------------- #
ARCANE = xpm.FORMATS["arcane"]


def test_arcane_mention_wins_over_name():
    p = xpm.parse_level_message(
        "<@111> has reached level **13**. GG!",
        [111],
        fmt=ARCANE,
    )
    assert p == xpm.ParsedLevelUp(level=13, user_id=111, name=None)


def test_arcane_plaintext_name_when_no_mention():
    p = xpm.parse_level_message(
        "@Menno420 has reached level 13. GG!",
        [],
        fmt=ARCANE,
    )
    assert p == xpm.ParsedLevelUp(level=13, name="Menno420")


def test_arcane_name_without_at_sign():
    p = xpm.parse_level_message("Nicely has reached level 3. GG!", [], fmt=ARCANE)
    assert p == xpm.ParsedLevelUp(level=3, name="Nicely")


def test_arcane_bold_and_spacing_tolerated():
    assert xpm.parse_level_message("x has reached  level   7", [], fmt=ARCANE).level == 7
    assert (
        xpm.parse_level_message("x has reached level **7**", [], fmt=ARCANE).level == 7
    )


def test_non_levelup_message_returns_none():
    assert xpm.parse_level_message("just chatting", [], fmt=ARCANE) is None
    assert xpm.parse_level_message("", [], fmt=ARCANE) is None


def test_first_mention_is_the_subject():
    p = xpm.parse_level_message(
        "<@111> has reached level 5. GG!",
        [111, 222],
        fmt=ARCANE,
    )
    assert p.user_id == 111


# --------------------------------------------------------------------------- #
# parse_level_message — other announcers
# --------------------------------------------------------------------------- #
def test_mee6_advanced_to_level():
    mee6 = xpm.FORMATS["mee6"]
    p = xpm.parse_level_message(
        "GG @user, you just advanced to level **5**!",
        [222],
        fmt=mee6,
    )
    assert (p.level, p.user_id) == (5, 222)


def test_mee6_name_fallback_strips_gg_prefix():
    mee6 = xpm.FORMATS["mee6"]
    p = xpm.parse_level_message(
        "GG SomeName, you just advanced to level 5!",
        [],
        fmt=mee6,
    )
    assert p == xpm.ParsedLevelUp(level=5, name="SomeName")


def test_superbot_own_announce():
    sb = xpm.FORMATS["superbot"]
    p = xpm.parse_level_message("<@9> reached **Level 4**!", [9], fmt=sb)
    assert (p.level, p.user_id) == (4, 9)


def test_generic_matches_any_level_phrase():
    gen = xpm.FORMATS["generic"]
    p = xpm.parse_level_message("welcome to level 2, friend", [], fmt=gen)
    assert p is not None and p.level == 2


# --------------------------------------------------------------------------- #
# reduce_max_levels
# --------------------------------------------------------------------------- #
def test_reduce_keeps_highest_level_per_user():
    assert xpm.reduce_max_levels([(1, 3), (1, 13), (2, 4), (1, 7)]) == {1: 13, 2: 4}


def test_reduce_empty():
    assert xpm.reduce_max_levels([]) == {}


# --------------------------------------------------------------------------- #
# ScanPlan
# --------------------------------------------------------------------------- #
def test_scan_plan_user_count():
    plan = xpm.ScanPlan(
        source_key="arcane",
        source_label="Arcane",
        channel_id=5,
        scanned_messages=100,
        matched=40,
        records=((1, 3), (2, 13)),
    )
    assert plan.user_count == 2
