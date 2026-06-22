"""BTD6 per-round XP — the bloonswiki-sourced base-XP table + modifiers.

XP-per-round is NOT in the BTD Mod Helper game data dump (round files store only
bloon composition + timing). BTD6 awards a FIXED amount per round number, given
by a piecewise-linear formula. These tests pin the parser's formula against the
exact values from bloonswiki's own "Base XP" round-table column (the validation
oracle, mirroring how round *cash* is pinned to cyberquincy), the runtime loader,
and the difficulty / freeplay modifier math.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).parents[3]
_DISBOT = _REPO / "disbot"
_SCRIPTS = _REPO / "scripts"
for _p in (_DISBOT, _SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import parse_gamedata  # noqa: E402

from services import btd6_data_service  # noqa: E402

# bloonswiki "Base XP" column (List_of_rounds_in_BTD6), captured 2026-06-22.
# Every band boundary of the piecewise formula is represented.
_WIKI_BASE_XP = {
    1: 40,
    2: 60,
    5: 120,
    10: 220,
    11: 240,
    19: 400,
    20: 420,  # last round of band 1 (20r + 20)
    21: 460,  # first round of band 2 (40(r-20) + 420)
    22: 500,
    49: 1580,
    50: 1620,  # last round of band 2
    51: 1710,  # first round of band 3 (90(r-50) + 1620)
    52: 1800,
    99: 6030,
    100: 6120,
}


@pytest.fixture(autouse=True)
def _reset_dataset_cache():
    btd6_data_service.reset_cache()
    yield
    btd6_data_service.reset_cache()


# --- the formula (parse_gamedata._round_base_xp) -------------------------------


@pytest.mark.parametrize(("rnd", "xp"), sorted(_WIKI_BASE_XP.items()))
def test_formula_matches_the_wiki_base_xp_column(rnd: int, xp: int):
    assert parse_gamedata._round_base_xp(rnd) == xp


def test_formula_is_continuous_across_band_boundaries():
    # No jump in slope between bands: band 1 ends and band 2 begins at +40/round,
    # band 2 ends and band 3 begins at +90/round.
    assert parse_gamedata._round_base_xp(21) - parse_gamedata._round_base_xp(20) == 40
    assert parse_gamedata._round_base_xp(51) - parse_gamedata._round_base_xp(50) == 90


# --- the generated payload (parse_gamedata.build_round_xp) ---------------------


def test_payload_covers_rounds_1_to_140_with_formula_values():
    payload = parse_gamedata.build_round_xp()
    rows = payload["rounds"]
    assert [r["round"] for r in rows] == list(range(1, 141))
    for row in rows:
        assert row["xp"] == parse_gamedata._round_base_xp(row["round"])


def test_payload_carries_the_modifier_constants():
    payload = parse_gamedata.build_round_xp()
    assert payload["difficulty_multipliers"] == {
        "beginner": 1.0,
        "intermediate": 1.1,
        "advanced": 1.2,
        "expert": 1.3,
    }
    assert payload["freeplay_multipliers"] == {
        "through_round_100": 0.3,
        "round_101_plus": 0.1,
    }


def test_committed_round_xp_json_matches_the_generator():
    # The committed data file must be exactly what the generator produces, so a
    # drifted file is caught here instead of in production.
    import json

    committed = json.loads(
        (_DISBOT / "data" / "btd6" / "round_xp.json").read_text("utf-8"),
    )
    assert committed["rounds"] == parse_gamedata.build_round_xp()["rounds"]


# --- the runtime loader + helpers ----------------------------------------------


def test_dataset_loads_round_xp_table():
    dataset = btd6_data_service.get_dataset()
    assert len(dataset.round_xp) == 140
    by_round = {e.round_number: e.base_xp for e in dataset.round_xp}
    for rnd, xp in _WIKI_BASE_XP.items():
        assert by_round[rnd] == xp
    assert "round_xp" in dataset.sources


def test_round_base_xp_helper():
    assert btd6_data_service.round_base_xp(1) == 40
    assert btd6_data_service.round_base_xp(100) == 6120
    assert btd6_data_service.round_base_xp(9999) is None


def test_round_xp_earned_applies_difficulty():
    # Round 10 base = 220; Expert ×1.3 = 286.
    assert btd6_data_service.round_xp_earned(10) == 220
    assert btd6_data_service.round_xp_earned(10, difficulty="expert") == 286
    assert btd6_data_service.round_xp_earned(10, difficulty="intermediate") == 242


def test_round_xp_earned_applies_freeplay():
    # Round 100 base = 6120; freeplay through 100 → ×0.30 = 1836.
    assert btd6_data_service.round_xp_earned(100, freeplay=True) == 1836
    # Round 101+ in freeplay → ×0.10.
    base_101 = btd6_data_service.round_base_xp(101)
    assert base_101 is not None
    assert btd6_data_service.round_xp_earned(101, freeplay=True) == round(
        base_101 * 0.1,
        2,
    )


def test_round_xp_earned_unknown_round_is_none():
    assert btd6_data_service.round_xp_earned(9999) is None
