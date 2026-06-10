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
    assert all("source: BTD6 game data" in ln for ln in stat_lines)
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


def test_economy_tower_emits_income_but_no_damage_lines():
    # Since the Q-0067 cutover the Farm has full game-native tiers: its nominal
    # banana "attack" is suppressed (no damage/pierce lines), while real
    # economy facts ground (Wall Street's $4,000/round, the IMF Loan ability).
    lines = ctx._render_fixture_tower(ds.get_tower("banana_farm"))
    stat_lines = [ln for ln in lines if "btd6_tower_stats" in ln]
    assert not [ln for ln in stat_lines if "dmg" in ln or "pierce" in ln]
    assert any("Income $4,000/round" in ln for ln in stat_lines)


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
    assert all("source: BTD6 game data" in ln for ln in stat_lines)


def test_game_data_hero_grounds_cost_and_per_level_stat_lines():
    # Obyn attacks in-game; bloonswiki had no stats module for him, but the
    # game-data export does, so grounding now carries btd6_hero_stats lines too.
    lines = ctx._render_fixture_hero(ds.get_hero("obyn_greenfoot"))
    assert any("[btd6_hero]" in ln for ln in lines)
    assert any("btd6_hero_stats" in ln for ln in lines)


def test_bloon_grounding_includes_rbe_and_speed():
    # The new structured bloon facts (RBE / speed) reach the model, bounded to a
    # couple of bits per bloon.
    lines = ctx._render_fixture_bloon(ds.get_bloon("ceramic"))
    blob = " ".join(lines)
    assert "RBE" in blob
    assert "speed:" in blob


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


def test_bloon_grounding_includes_fortified_rbe():
    # The fortified-ZOMG question that prompted this work: fortified RBE must
    # reach the model, not just the base RBE.
    zomg = ds.get_bloon("zomg")
    blob = " ".join(ctx._render_fixture_bloon(zomg))
    assert "fortified" in blob
    assert str(zomg.rbe_fortified) in blob


def test_round_grounding_has_composition_and_rbe():
    lines = ctx._render_fixture_round(ds.get_round(63))
    blob = " ".join(lines)
    assert "[btd6_round] Round 63" in blob
    assert "RBE" in blob
    assert "composition" in blob
    assert "Lead" in blob and "Ceramic" in blob


def test_crosspaths_in_text_is_bounded():
    cx = ctx._crosspaths_in_text
    assert cx("0-2-5 ninja") == ["025"]
    assert cx("025 ninja") == ["025"]
    assert cx("2-0-5 and 0-5-2") == ["205", "052"]
    # Single-path codes, round numbers and version strings must not fire.
    assert cx("200 dart") == []
    assert cx("round 100 has a bad") == []
    assert cx("version 54.2 dart") == []


async def test_named_crosspath_is_grounded():
    context = await ctx.build("what's the pierce of a 0-2-5 ninja")
    blob = "\n".join(context.facts)
    assert "Ninja Monkey" in blob
    assert "(0-2-5)" in blob  # the specifically-named crosspath's stats surface


def test_named_crosspath_surfaces_crosspath_specific_zone_effect():
    # A named crosspath must surface its OWN buff/zone effects, not just headline
    # stats: Heli 0-1-4's MOAB Shove is stronger (MOAB -0.51) than the 0-0-4 base
    # (-0.4). Both stored; the crosspath grounding must reach the named one.
    cross = "\n".join(ctx._render_tower_crosspath("heli_pilot", "Heli Pilot", "014"))
    base = "\n".join(ctx._render_tower_crosspath("heli_pilot", "Heli Pilot", "004"))
    assert "[btd6_tower_stats effect]" in cross
    assert "MOAB-class shoved backward at x-0.51 speed" in cross
    assert "x-0.51" not in base and "x-0.4" in base  # base path keeps its own value
