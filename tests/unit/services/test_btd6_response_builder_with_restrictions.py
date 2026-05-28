"""``for_tower`` / ``for_hero`` with the new ``restrictions`` kwarg.

The restriction strings land in ``BTD6Response.live_facts`` so the
existing renderer (`response_to_embed`) surfaces them in the "Live
data" field. Back-compat: passing no ``restrictions`` keeps
``live_facts`` empty, which is what static-only callers
(``deterministic_answer``) rely on.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from services.btd6_live_query_service import TowerRestrictionContext
from services.btd6_response_builder import (
    _format_restriction_lines,
    for_hero,
    for_tower,
)


def _ctx(
    *,
    event_kind="btd6_race",
    event_name="Reversed Loop",
    end_ms=None,
    stance="banned",
    max_count=0,
    p1=0,
    p2=0,
    p3=0,
    is_hero=False,
    sentinel=False,
) -> TowerRestrictionContext:
    return TowerRestrictionContext(
        event_kind=event_kind,
        event_id="abc",
        event_name=event_name,
        end_ms=end_ms,
        fetched_at=datetime.now(tz=timezone.utc),
        stance=stance,
        max_count=max_count,
        path1_blocked=p1,
        path2_blocked=p2,
        path3_blocked=p3,
        is_hero=is_hero,
        sentinel_all_heroes_banned=sentinel,
    )


def _future_ms(hours: int) -> int:
    return int(
        (datetime.now(tz=timezone.utc) + timedelta(hours=hours)).timestamp() * 1000
    )


def test_format_restriction_lines_banned():
    out = _format_restriction_lines((_ctx(stance="banned"),))
    assert out
    assert "BANNED" in out[0]
    assert "race" in out[0]
    assert "Reversed Loop" in out[0]


def test_format_restriction_lines_limited_renders_max_and_paths():
    out = _format_restriction_lines(
        (_ctx(stance="limited", max_count=3, p1=2, p3=4),),
    )
    assert "LIMITED" in out[0]
    assert "max 3" in out[0]
    assert "path1 top 2" in out[0]
    assert "path3 top 4" in out[0]


def test_format_restriction_lines_path_blocked():
    out = _format_restriction_lines(
        (_ctx(stance="path_blocked", max_count=None, p1=3, p2=0, p3=1),),
    )
    assert "blocked" in out[0]
    assert "path1 top 3" in out[0]
    assert "path3 top 1" in out[0]


def test_format_restriction_lines_sentinel_all_heroes_banned():
    out = _format_restriction_lines((_ctx(sentinel=True, is_hero=True),))
    assert "ALL HEROES BANNED" in out[0]


def test_format_restriction_lines_skips_allowed():
    out = _format_restriction_lines(
        (
            _ctx(stance="allowed", max_count=None),
            _ctx(stance="banned", event_name="Boss X"),
        ),
    )
    assert len(out) == 1
    assert "Boss X" in out[0]


def test_format_restriction_lines_ends_in_h_suffix():
    out = _format_restriction_lines(
        (_ctx(stance="banned", end_ms=_future_ms(14)),),
    )
    assert "ends in" in out[0]
    # 13h or 14h depending on timing of the int-div rollover.
    assert "13h" in out[0] or "14h" in out[0]


@pytest.mark.parametrize(
    "kind,label",
    [
        ("btd6_boss_difficulty", "boss"),
        ("btd6_odyssey_difficulty", "odyssey"),
        ("btd6_challenge", "challenge"),
    ],
)
def test_format_restriction_lines_uses_friendly_kind_label(kind, label):
    out = _format_restriction_lines((_ctx(event_kind=kind, stance="banned"),))
    assert label in out[0]


# ---------------------------------------------------------------------------
# for_tower / for_hero back-compat — restrictions kwarg is optional.
# ---------------------------------------------------------------------------


class _StubFact:
    """Minimal TowerFact stand-in for builder tests."""

    class _Tower:
        canonical = "Dart Monkey"
        description = "Cheap monkey."
        category = "primary"
        upgrade_paths = {"path1": ("a", "b", "c", "d", "e")}
        upgrade_costs = {"path1": (100, 200, 300, 400, 500)}
        wiki_url = "https://example.invalid/dart"

    tower = _Tower()
    base_cost = 200


class _StubHero:
    canonical = "Quincy"
    description = "Archer hero."
    base_cost = 750
    wiki_url = "https://example.invalid/quincy"

    class _Ability:
        level = 3
        name = "Storm of Arrows"
        summary = "Burst attack."

    abilities = (_Ability(),)


def test_for_tower_no_restrictions_leaves_live_facts_empty():
    resp = for_tower(_StubFact())
    assert resp.live_facts == ()


def test_for_tower_renders_per_tier_upgrade_costs():
    resp = for_tower(_StubFact())
    # One field per non-empty upgrade path, with per-tier costs inline.
    assert resp.fields
    _label, value = resp.fields[0]
    assert "a ($100)" in value
    assert "e ($500)" in value
    assert "→" in value


def test_for_tower_falls_back_when_description_empty():
    class _NoDescFact(_StubFact):
        class _Tower(_StubFact._Tower):
            description = ""

        tower = _Tower()

    resp = for_tower(_NoDescFact())
    assert resp.short_answer
    assert "$200" in resp.short_answer


def test_for_tower_with_restrictions_populates_live_facts():
    resp = for_tower(
        _StubFact(),
        restrictions=(_ctx(stance="banned"),),
    )
    assert resp.live_facts
    assert "BANNED" in resp.live_facts[0]


def test_for_hero_no_restrictions_leaves_live_facts_empty():
    resp = for_hero(_StubHero())
    assert resp.live_facts == ()


def test_for_hero_with_sentinel_renders_all_heroes_banned():
    resp = for_hero(
        _StubHero(),
        restrictions=(_ctx(sentinel=True, is_hero=True),),
    )
    assert resp.live_facts
    assert "ALL HEROES BANNED" in resp.live_facts[0]
