"""Unit tests for services/btd6_estimator_service.py.

Exercised against the real committed BTD6 data (deterministic), like the rest of
the btd6 suite. Pins: cost-to-crosspath, base-DPS with the instakill-sentinel
filter, the kill-time = HP/DPS estimate, damage-type immunity blocking, the
query parser, and that the cheapest-counters ranking is not polluted by
instakill values (the Druid Vine 9,999,999 sentinel).
"""

from __future__ import annotations

import sys
from pathlib import Path

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_estimator_service as est  # noqa: E402
from services import btd6_stats_service as stats  # noqa: E402


def _dart():
    return stats.get_tower_stats("dart_monkey")


# --------------------------------------------------------------------- cost


def test_cost_for_code_base_and_upgrades() -> None:
    dart = _dart()
    # base (000) is just the base cost; a path-1 tier-1 adds Sharp Shots' cost.
    assert est.cost_for_code(dart, "000") == dart.base_cost
    cost_100 = est.cost_for_code(dart, "100")
    assert cost_100 is not None and cost_100 > dart.base_cost


def test_cost_for_code_rejects_malformed() -> None:
    assert est.cost_for_code(_dart(), "999") is None  # illegal tiers
    assert est.cost_for_code(_dart(), "xyz") is None


# ---------------------------------------------------------------------- dps


def test_dps_base_dart_is_sane() -> None:
    # Dart Monkey base: 1 damage / 0.95s ≈ 1.05 DPS.
    dps = est.dps_for_code(_dart(), "000")
    assert dps is not None and 0.8 < dps < 1.5


def test_instakill_sentinel_is_filtered() -> None:
    # Druid 0-3-0 (Druid of the Storm line) carries the 9,999,999 Vine sentinel;
    # it must NOT produce millions of DPS.
    druid = stats.get_tower_stats("druid")
    if druid is None or not druid.tier("030"):
        return  # data shape changed; nothing to assert
    dps = est.dps_for_code(druid, "030")
    assert dps is not None and dps < 100_000


# ----------------------------------------------------------------- estimate


def test_estimate_kill_time_is_hp_over_dps() -> None:
    e = est.estimate("super_monkey", "000", "bloonarius", 5)
    assert e is not None
    assert e.boss_hp == 3_000_000
    assert e.dps > 0 and not e.blocked_by_immunity
    # time_to_kill ≈ hp / dps (allow rounding).
    assert e.time_to_kill_s == round(e.boss_hp / e.dps, 1)


def test_estimate_blocks_on_damage_type_immunity() -> None:
    # Wizard's base magic bolts are Energy; Blastapopoulos (Purple props) is
    # immune to Energy → can't damage it.
    e = est.estimate("wizard_monkey", "000", "blastapopoulos", 5)
    assert e is not None
    assert "Energy" in e.boss_immune_to
    assert e.blocked_by_immunity is True
    assert e.time_to_kill_s is None


def test_estimate_unknown_returns_none() -> None:
    assert est.estimate("super_monkey", "000", "no_such_boss", 5) is None
    assert est.estimate("no_such_tower", "000", "bloonarius", 5) is None


# ------------------------------------------------------------------- parser


def test_parse_request_single_with_tier() -> None:
    req = est.parse_request("super monkey 0-4-0 vs bloonarius t5")
    assert req.mode == "single"
    assert "super monkey" in req.tower_query
    assert "bloonarius" in req.boss_query
    assert "t5" not in req.boss_query.lower()  # tier stripped out
    assert req.tier == 5


def test_parse_request_counters_and_default_tier() -> None:
    req = est.parse_request("counters for bloonarius tier 3")
    assert req.mode == "counters"
    assert req.boss_query == "bloonarius"
    assert req.tier == 3
    # default tier when none named.
    assert est.parse_request("vortex").tier == 5


# ----------------------------------------------------------------- counters


def test_cheapest_counters_sorted_and_not_instakill_polluted() -> None:
    rows = est.cheapest_counters("bloonarius", 5, limit=5)
    assert rows, "expected some ranked counters"
    # sorted by dps_per_dollar descending.
    values = [r.dps_per_dollar for r in rows]
    assert values == sorted(values, reverse=True)
    # the top entry must be a sane sustained-DPS value, not the 9,999,999 Vine.
    assert rows[0].dps < 100_000


# --------------------------------------------------------------- formatting


def test_format_estimate_text_contains_key_numbers() -> None:
    e = est.estimate("super_monkey", "000", "bloonarius", 5)
    text = est.format_estimate_text(e)
    assert "Bloonarius" in text and "3,000,000" in text
    assert "Estimate" in text  # the assumptions line


def test_format_estimate_text_blocked_path() -> None:
    e = est.estimate("wizard_monkey", "000", "blastapopoulos", 5)
    text = est.format_estimate_text(e)
    assert "immune" in text.lower()


def test_format_counters_text_lists_towers() -> None:
    rows = est.cheapest_counters("bloonarius", 5, limit=3)
    text = est.format_counters_text(rows, "Bloonarius", 5)
    assert "Bloonarius" in text and "DPS" in text


def test_resolve_and_estimate_free_form() -> None:
    e = est.resolve_and_estimate("super monkey 0-4-0", "bloonarius", 5)
    assert e is not None and e.crosspath == "0-4-0"


def test_find_boss_by_name() -> None:
    boss = est.find_boss("how do I beat bloonarius")
    assert boss is not None and boss.id == "bloonarius"
    assert est.find_boss("nonsense xyz") is None
