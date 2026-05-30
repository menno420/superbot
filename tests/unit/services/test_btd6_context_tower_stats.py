"""The AI grounding includes per-tier tower stats, tagged normal."""

from __future__ import annotations

import pytest

from services import btd6_context_service as ctx
from services import btd6_data_service as ds
from services import btd6_stats_service as ss


@pytest.fixture(autouse=True)
def _fresh():
    ds.reset_cache()
    ss.reset_cache()
    yield
    ds.reset_cache()
    ss.reset_cache()


def test_combat_tower_emits_tagged_stat_lines():
    import re

    from utils.btd6 import tier_codes

    lines = ctx._render_fixture_tower(ds.get_tower("bomb_shooter"))
    stat_lines = [ln for ln in lines if "[btd6_tower_stats normal]" in ln]
    assert len(stat_lines) == 16  # base + 15 single-path tiers
    assert all("source: bloonswiki" in ln for ln in stat_lines)
    assert any("Bloon Crush" in ln and "Normal" in ln for ln in stat_lines)
    # Grounding stays bounded: only single-path tiers reach the model, never the
    # ~48 reconstructed crosspaths (which would bloat the prompt).
    codes = [
        m.replace("-", "")
        for ln in stat_lines
        for m in re.findall(r"\((\d-\d-\d)\)", ln)
    ]
    assert codes
    assert all(c in tier_codes.SINGLE_PATH_CODES for c in codes)


def test_income_and_infinity_render():
    lines = ctx._render_fixture_tower(ds.get_tower("druid"))
    sof = next(ln for ln in lines if "0-5-0" in ln)
    assert "Income $1,000/round" in sof
    assert "∞" in sof  # 9,999,999 sentinel rendered as infinity
    assert "9999999" not in sof


def test_economy_tower_emits_no_combat_stat_lines():
    lines = ctx._render_fixture_tower(ds.get_tower("banana_farm"))
    assert not [ln for ln in lines if "btd6_tower_stats" in ln]


# --- regression: the lead-immunity + camo-detection facts were extracted by
# normal_stats() but dropped from the grounding line; they must reach the model.


def test_attacking_tier_lines_carry_immunity_and_camo():
    lines = ctx._render_fixture_tower(ds.get_tower("dart_monkey"))
    base = next(ln for ln in lines if "(0-0-0)" in ln and "tower_stats" in ln)
    # The Dart Monkey deals Sharp damage and cannot pop Lead unupgraded.
    assert "Sharp" in base
    assert "Lead" in base  # the cannot-pop note, folded into the damage bit
    # Camo detection is now surfaced (Dart Monkey base cannot see camo).
    assert "Camo" in base


def test_camo_detecting_tower_marked_sees_camo():
    lines = ctx._render_fixture_tower(ds.get_tower("ninja_monkey"))
    stat_lines = [ln for ln in lines if "tower_stats" in ln]
    # Ninja Monkey has innate camo detection at every tier.
    assert any("sees Camo" in ln for ln in stat_lines)


def test_hero_with_module_emits_per_level_stat_lines():
    lines = ctx._render_fixture_hero(ds.get_hero("quincy"))
    stat_lines = [ln for ln in lines if "[btd6_hero_stats normal]" in ln]
    assert any("Level 1" in ln for ln in stat_lines)
    assert any("Level 20" in ln for ln in stat_lines)
    assert all("source: bloonswiki" in ln for ln in stat_lines)


def test_hero_without_module_has_cost_and_abilities_but_no_stat_lines():
    # Obyn attacks in-game but has no bloonswiki stats module → cost + abilities
    # only, no per-level stat lines (and no crash).
    lines = ctx._render_fixture_hero(ds.get_hero("obyn_greenfoot"))
    assert not [ln for ln in lines if "btd6_hero_stats" in ln]
    assert any("[btd6_hero]" in ln for ln in lines)


async def test_grounded_build_surfaces_bloon_immunity_and_tower_facts():
    # End-to-end through the real grounding builder (DB passes degrade to
    # no-ops without a pool; the fixture pass always runs). This is the guard
    # the memory-only eval cases never gave us.
    context = await ctx.build("can an unupgraded dart monkey pop a lead bloon?")
    blob = "\n".join(context.facts)
    assert "[btd6_bloon] Lead Bloon" in blob
    assert "immune to Sharp" in blob
    # And the tower-side fact that answers the same question.
    assert "Cannot damage Lead" in blob
