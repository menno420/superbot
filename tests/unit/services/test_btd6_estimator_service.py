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


# ------------------------------------------------------- track length (RBS)


def test_find_map_track_resolves_and_misses() -> None:
    track = est.find_map_track("how long to beat bloonarius on monkey meadow")
    assert track is not None
    name, rbs = track
    assert name == "Monkey Meadow" and 30 < rbs < 35  # 32.745 from the wiki
    assert est.find_map_track("no known map here") is None


def test_parse_request_extracts_map() -> None:
    req = est.parse_request("super monkey 0-4-0 vs bloonarius t5 on monkey meadow")
    assert req.map_query == "Monkey Meadow"
    # the map text is stripped out of the boss query.
    assert "meadow" not in req.boss_query.lower()
    assert "bloonarius" in req.boss_query.lower()


def test_estimate_with_map_fills_escape_margin() -> None:
    e = est.estimate("dartling_gunner", "520", "bloonarius", 5, map_query="monkey meadow")
    assert e is not None
    assert e.map_canonical == "Monkey Meadow"
    assert e.track_rbs is not None and 30 < e.track_rbs < 35
    # boss crosses in ~rbs / boss_speed.
    assert e.boss_cross_s == round(e.track_rbs / e.boss_speed, 1)
    # kills_before_exit reflects ttk vs boss_cross_s.
    if e.time_to_kill_s is not None:
        assert e.kills_before_exit == (e.time_to_kill_s <= e.boss_cross_s)


def test_estimate_without_map_has_no_track_fields() -> None:
    e = est.estimate("super_monkey", "000", "bloonarius", 5)
    assert e is not None
    assert e.map_canonical is None and e.track_rbs is None
    assert e.boss_cross_s is None and e.kills_before_exit is None


def test_format_estimate_includes_track_line() -> None:
    e = est.estimate("super_monkey", "040", "bloonarius", 5, map_query="monkey meadow")
    text = est.format_estimate_text(e)
    assert "Monkey Meadow" in text and "red bloon" in text
    assert "~~" not in text  # no double-tilde


def test_track_data_integrity() -> None:
    """Every committed RBS track maps to a real map id, with a sane value."""
    import sys
    from pathlib import Path

    disbot = Path(__file__).parents[3] / "disbot"
    if str(disbot) not in sys.path:
        sys.path.insert(0, str(disbot))
    import json

    from services import btd6_data_service

    blob = json.loads(
        (disbot / "data" / "btd6" / "map_track_lengths.json").read_text(encoding="utf-8"),
    )
    map_ids = {m.id for m in btd6_data_service.get_dataset().maps}
    tracks = blob["tracks"]
    assert len(tracks) >= 50, "expected the full wiki RBS set"
    for t in tracks:
        assert t["map_id"] in map_ids, f"unknown map_id {t['map_id']!r}"
        assert 1.0 < t["rbs"] < 120.0, f"implausible RBS for {t['map_id']}: {t['rbs']}"
    # provenance is recorded (Q-0105 — sourced data must say where it came from).
    # NB: assert a non-host prefix, not a host substring, so CodeQL's
    # "incomplete URL substring sanitization" rule doesn't false-positive on a
    # provenance check (this is a data-source label, not an access-control gate).
    assert blob["source"].startswith("Bloons Wiki")
