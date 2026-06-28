"""Counting leaderboard — ranking math + the player-facing embeds.

Guards the fix that surfaces the previously-invisible per-channel leaderboard
(Counting completion-cert punch-list #2): the tally was incremented on every
accepted count but never displayed. These tests fail against the pre-fix state
(no ``top_counters`` / no leaderboard embeds existed).
"""

from __future__ import annotations

from types import SimpleNamespace

from cogs.counting import game_logic
from cogs.counting import leaderboard as counting_leaderboard


def _guild(names: dict[int, str]):
    """A minimal fake guild whose ``get_member`` resolves the given ids."""
    return SimpleNamespace(
        get_member=lambda mid: (
            SimpleNamespace(display_name=names[mid]) if mid in names else None
        ),
    )


# --------------------------------------------------------------------- top_counters


def test_top_counters_ranks_descending_and_drops_zero():
    ranked = game_logic.top_counters({"1": 3, "2": 7, "3": 0, "4": -1})
    assert ranked == [("2", 7), ("1", 3)]  # 0 and negative are dropped


def test_top_counters_tie_break_is_stable_by_user_id():
    ranked = game_logic.top_counters({"20": 5, "10": 5, "30": 5})
    assert ranked == [("10", 5), ("20", 5), ("30", 5)]


def test_top_counters_limit_and_unlimited():
    board = {str(i): i for i in range(1, 6)}  # 1..5
    assert game_logic.top_counters(board, limit=2) == [("5", 5), ("4", 4)]
    assert len(game_logic.top_counters(board, limit=0)) == 5  # <=0 == everything


def test_top_counters_empty():
    assert game_logic.top_counters({}) == []


# ----------------------------------------------------------------- leaderboard embed


def test_build_leaderboard_embed_lists_ranked_players():
    guild = _guild({1: "Alice", 2: "Bob"})
    channel = SimpleNamespace(name="counting")
    embed = counting_leaderboard.build_leaderboard_embed(
        guild,
        channel,
        {"1": 4, "2": 9},
    )
    assert "Counting Leaderboard" in embed.title
    assert "🥇 Bob — **9** counts" in embed.description
    assert "🥈 Alice — **4** counts" in embed.description


def test_build_leaderboard_embed_singular_count_unit():
    guild = _guild({1: "Solo"})
    channel = SimpleNamespace(name="c")
    embed = counting_leaderboard.build_leaderboard_embed(guild, channel, {"1": 1})
    assert "**1** count" in embed.description
    assert "**1** counts" not in embed.description


def test_build_leaderboard_embed_empty_is_friendly_not_a_dead_end():
    guild = _guild({})
    channel = SimpleNamespace(name="c")
    embed = counting_leaderboard.build_leaderboard_embed(guild, channel, {})
    assert "be the first" in embed.description.lower()


def test_unresolved_member_falls_back_to_user_id():
    guild = _guild({})  # nobody resolves
    channel = SimpleNamespace(name="c")
    embed = counting_leaderboard.build_leaderboard_embed(guild, channel, {"42": 3})
    assert "User 42" in embed.description


# ------------------------------------------------------------------- count_info field


def test_top_field_value_none_when_empty():
    assert counting_leaderboard.top_field_value(_guild({}), {}) is None


def test_top_field_value_caps_at_three_and_points_to_counttop():
    guild = _guild({i: f"P{i}" for i in range(1, 6)})
    value = counting_leaderboard.top_field_value(
        guild,
        {str(i): i for i in range(1, 6)},
    )
    assert value is not None
    # top-3 only (P5, P4, P3); P2/P1 excluded
    assert value.count("\n") == 3  # 3 player lines + the hint line
    assert "P5" in value and "P2" not in value
    assert "!counttop" in value
