"""Unit tests for ``_render_tower_restrictions``.

Decode the ``_towers`` array preserved verbatim in race/boss/odyssey
metadata bodies into UI categories. Tested in isolation so the
rendering logic can't drift relative to the parser shape.
"""

from __future__ import annotations

from cogs.btd6._builders import _render_tower_restrictions


def _entry(
    tower: str,
    *,
    max: int | None = None,
    p1: int = 0,
    p2: int = 0,
    p3: int = 0,
    is_hero: bool = False,
) -> dict:
    out: dict = {
        "tower": tower,
        "path1NumBlockedTiers": p1,
        "path2NumBlockedTiers": p2,
        "path3NumBlockedTiers": p3,
        "isHero": is_hero,
    }
    if max is not None:
        out["max"] = max
    return out


def test_empty_list_returns_empty_dict():
    assert _render_tower_restrictions([]) == {}


def test_max_zero_non_hero_is_banned():
    out = _render_tower_restrictions([_entry("BananaFarm", max=0)])
    assert out == {"banned": ["BananaFarm"]}


def test_max_positive_is_limited_with_count():
    out = _render_tower_restrictions([_entry("Alchemist", max=1)])
    assert out == {"limited": ["Alchemist (max 1)"]}


def test_hero_with_max_zero_is_heroes_banned():
    out = _render_tower_restrictions(
        [_entry("ChosenPrimaryHero", max=0, is_hero=True)],
    )
    assert out == {"heroes_banned": ["ChosenPrimaryHero"]}


def test_path_blocked_renders_per_path():
    out = _render_tower_restrictions(
        [_entry("DartMonkey", p1=2, p2=0, p3=4)],
    )
    assert "path_blocked" in out
    rendered = out["path_blocked"][0]
    assert "DartMonkey" in rendered
    assert "path1 top 2" in rendered
    assert "path3 top 4" in rendered
    assert "path2" not in rendered


def test_mixed_array_groups_into_all_categories():
    out = _render_tower_restrictions(
        [
            _entry("BananaFarm", max=0),
            _entry("Alchemist", max=1),
            _entry("DartMonkey", p1=3),
            _entry("ChosenPrimaryHero", max=0, is_hero=True),
            _entry("Quincy", max=1, is_hero=True),
        ],
    )
    assert out["banned"] == ["BananaFarm"]
    assert "Alchemist (max 1)" in out["limited"]
    # Quincy is a hero with max=1 — `isHero=True` only matters when
    # combined with max=0 (banned). With max>=1 the entry falls into
    # the regular "limited" bucket so the operator still sees the cap.
    assert "Quincy (max 1)" in out["limited"]
    assert any("DartMonkey" in s for s in out["path_blocked"])
    assert out["heroes_banned"] == ["ChosenPrimaryHero"]


def test_entries_without_tower_field_are_skipped():
    out = _render_tower_restrictions(
        [{"max": 0, "isHero": False}, _entry("DartMonkey", max=0)],
    )
    assert out == {"banned": ["DartMonkey"]}


def test_missing_max_with_no_path_block_is_no_op():
    """Entry with max=missing and no path blocks → no restriction."""
    out = _render_tower_restrictions([_entry("Ninja")])
    assert out == {}
