"""Alternate Bloons Rounds (abr_rounds.json) — fixture integrity + semantics.

The ABR sidecar is game-sourced (``parse_gamedata.py --abr-rounds`` over the
dump's ``Rounds/AlternateRoundSet/``) and mirrors the rounds.json row shape.
Nobody has to trust its derived numbers: cash is recomputed here from scratch
(composition x children-inclusive pop sizes x the decay bands committed in
``income_sets.json``, plus the $100 + n bonus) and compared to the stored
values — the same discipline as ``test_btd6_round_cash.py`` for the standard
set. Composition anchors pin the famous ABR facts straight from the dump
(r40 = one Fortified MOAB, r100 = a Fortified BAD, r1 = 10 Blues).

ABR-as-played semantics (abr_rounds.json:cash_source): the set is entered at
round 3 with the $650 Hard start and ends at round 80 (81+ freeplay); rounds
1-2 exist in data but are never played, so their cumulative_cash is null and
cumulative totals baseline at round 3.
"""

from __future__ import annotations

import functools
import json
from pathlib import Path

from services.btd6_data_service import (
    get_dataset,
    get_round,
    resolve_roundset,
    round_cash,
    round_composition,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DATA = _REPO_ROOT / "disbot" / "data" / "btd6"

_ABR_STARTING_CASH = 650.0
_ABR_START_ROUND = 3


# ---------------------------------------------------------------------------
# Fixture integrity
# ---------------------------------------------------------------------------


def test_abr_fixture_loads_140_rounds_and_default_set_is_untouched():
    ds = get_dataset()
    assert len(ds.abr_rounds) == 140
    assert all(r.roundset == "alternate" for r in ds.abr_rounds)
    # The standard set is exactly as before — separate file, separate field.
    assert len(ds.rounds) == 140
    assert all(r.roundset == "default" for r in ds.rounds)
    assert "abr_rounds" in ds.sources
    assert "game data export" in ds.sources["abr_rounds"]


def test_abr_composition_anchors_match_the_dump_facts():
    by_n = {r.round_number: r for r in get_dataset().abr_rounds}
    # ABR r1: 10 Blues (never played, but the data row exists).
    assert [(g["bloon_id"], g["count"]) for g in by_n[1].groups] == [("blue", 10)]
    # The famous ABR round 40: a single Fortified MOAB (default r40 is plain).
    assert [(g["bloon_id"], g["modifiers"], g["count"]) for g in by_n[40].groups] == [
        ("moab", ["fortified"], 1),
    ]
    # ABR r100: one Fortified BAD (default r100 is a plain BAD).
    assert [(g["bloon_id"], g["modifiers"], g["count"]) for g in by_n[100].groups] == [
        ("bad", ["fortified"], 1),
    ]
    # Every group decomposes onto known bloon ids (no ABR-only entries needed).
    known = {b.id for b in get_dataset().bloons}
    for r in get_dataset().abr_rounds:
        for g in r.groups:
            assert g["bloon_id"] in known, f"r{r.round_number}: {g['bloon_id']}"


# ---------------------------------------------------------------------------
# Derived-number recompute (cash + cumulative), bands from income_sets.json
# ---------------------------------------------------------------------------


def _pop_size_table() -> dict[str, int]:
    bloons = {b.id: b for b in get_dataset().bloons}

    @functools.lru_cache(maxsize=None)
    def pop_size(bid: str) -> int:
        total = 1
        for child in bloons[bid].children_list:
            total += int(child["count"]) * pop_size(str(child["bloon_id"]))
        return total

    return {bid: pop_size(bid) for bid in bloons}


def _default_income_bands() -> tuple[list[tuple[int, float]], float]:
    raw = json.loads((_DATA / "income_sets.json").read_text("utf-8"))
    default = next(
        s for s in raw["income_sets"] if s["id"] == "default_income_set"
    )
    bands = [(int(t["threshold"]), float(t["multiplier"])) for t in default["thresholds"]]
    return bands, float(default["final_multiplier"])


def test_income_sets_default_bands_match_the_standard_cash_table():
    # Drift guard: the committed sourced bands must equal the v55 decay the
    # standard-set recompute (test_btd6_round_cash._cash_per_pop) hardcodes.
    bands, final = _default_income_bands()
    assert bands == [(50, 1.0), (60, 0.5), (85, 0.2), (100, 0.1), (120, 0.05), (140, 0.04)]
    assert final == 0.02


def test_stored_abr_cash_matches_recomputed_from_composition():
    pop = _pop_size_table()
    bands, final = _default_income_bands()

    def cash_per_pop(n: int) -> float:
        for threshold, multiplier in bands:
            if n <= threshold:
                return multiplier
        return final

    for r in get_dataset().abr_rounds:
        pop_count = sum(int(g["count"]) * pop[str(g["bloon_id"])] for g in r.groups)
        expected = round(pop_count * cash_per_pop(r.round_number) + (100 + r.round_number), 2)
        assert r.cash == expected, (
            f"ABR round {r.round_number}: stored cash={r.cash} but the "
            f"composition implies {expected}"
        )


def test_abr_cumulative_is_null_before_entry_then_runs_from_hard_start():
    cumulative = _ABR_STARTING_CASH
    for r in get_dataset().abr_rounds:
        if r.round_number < _ABR_START_ROUND:
            assert r.cumulative_cash is None, (
                f"ABR round {r.round_number} is never played — cumulative must be null"
            )
            continue
        assert r.cash is not None
        cumulative = round(cumulative + r.cash, 2)
        assert r.cumulative_cash == cumulative, (
            f"ABR round {r.round_number}: stored cumulative {r.cumulative_cash} "
            f"!= running total {cumulative}"
        )


# ---------------------------------------------------------------------------
# Service semantics (roundset selection)
# ---------------------------------------------------------------------------


def test_resolve_roundset_aliases():
    assert resolve_roundset("default") == "default"
    assert resolve_roundset("Standard") == "default"
    assert resolve_roundset("abr") == "alternate"
    assert resolve_roundset("ABR") == "alternate"
    assert resolve_roundset("alternate") == "alternate"
    assert resolve_roundset("Alternate Bloons Rounds") == "alternate"
    assert resolve_roundset("nonsense") is None


def test_get_round_selects_the_requested_set():
    assert get_round(40).groups[0]["modifiers"] == []
    assert get_round(40, "abr").groups[0]["modifiers"] == ["fortified"]
    assert get_round(40, "nonsense") is None


def test_round_composition_abr_carries_set_and_note():
    res = round_composition(40, roundset="abr")
    assert res["found"] is True
    assert res["roundset"] == "alternate"
    # A human label travels with the set so an ABR round figure can never read as
    # standard (the same round number differs between sets).
    assert res["roundset_label"] == "alternate (ABR)"
    assert "round 3" in res["note"]
    assert res["rounds"][0]["groups"] == [{"bloon": "moab", "count": 1}]
    # Default calls keep their values; they now also carry the standard label.
    base = round_composition(40)
    assert base["roundset"] == "default"
    assert base["roundset_label"] == "standard"
    assert "note" not in base


def test_round_composition_grounds_total_bloons_entering():
    # "How many bloons spawn on rN" must have a grounded total instead of
    # forcing the model to sum the groups (which tripped the faithfulness guard).
    res = round_composition(63)
    assert res["found"] is True
    first = res["rounds"][0]
    assert first["round"] == 63
    expected = sum(g["count"] for g in first["groups"])
    assert first["bloons_entering"] == expected
    # The range total is the sum of every round's entering bloons.
    assert res["total_bloons_entering"] == expected


def test_round_composition_rejects_unknown_set():
    res = round_composition(40, roundset="frontier")
    assert res["found"] is False
    assert "unknown round set" in res["note"]


def test_round_cash_abr_single_round_and_range():
    single = round_cash(40, roundset="abr")
    assert single["found"] is True
    assert single["roundset"] == "alternate"
    assert single["starting_cash"] == _ABR_STARTING_CASH
    assert "round 3" in single["assumptions"]

    ranged = round_cash(3, 80, roundset="abr")
    assert ranged["found"] is True
    assert ranged["inclusive"] is True
    assert ranged["cumulative_before_start"] == _ABR_STARTING_CASH
    # The subtraction identity holds for fully-played ABR ranges.
    assert ranged["range_cash"] == round(
        ranged["cumulative_at_end"] - ranged["cumulative_before_start"], 2
    )


def test_round_cash_abr_unplayed_rounds_disclose_the_boundary():
    r1 = round_cash(1, roundset="abr")
    assert r1["found"] is True
    assert r1["round_cash"] is not None
    assert r1["cumulative_cash"] is None
    assert "never played" in r1["cumulative_note"]

    ranged = round_cash(1, 5, roundset="abr")
    assert ranged["found"] is True
    assert "cumulative_note" in ranged
    # range_cash still sums exactly the requested rounds' data.
    per = {p["round"]: p["cash"] for p in ranged["per_round"]}
    assert ranged["range_cash"] == round(sum(per.values()), 2)


def test_round_cash_default_behaviour_unchanged():
    # The Q-0043 anchor and the default-set result shape are untouched.
    res = round_cash(50, 60)
    assert res["range_cash"] == 19840
    assert res["roundset"] == "default"
    assert "cumulative_note" not in res
    assert round_cash(80, 80) == round_cash(80)
