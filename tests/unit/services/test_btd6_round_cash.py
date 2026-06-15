"""Per-round cash consistency for the BTD6 round dataset.

Nobody has to trust a hand-typed cash number: we recompute every round's
``cash`` from scratch — pop_count (the round's spawn composition x each bloon's
total pop-count, bottoming out at Red) times the v55 cash-per-pop decay, plus
the ``$100 + n`` end-of-round bonus — and assert it equals the value stored in
``rounds.json``. A typo in the composition, a child tree, or the decay bands
makes the two disagree and fails CI.

This is the cash analogue of ``test_btd6_rbe.py`` (RBE is *health*-weighted; cash
is *pop*-weighted — a MOAB is 1 pop but 200 RBE, which is exactly why cash !=
RBE once blimps appear). Cross-validated against the cyberquincy data set: rounds
1-80 match 80/80. Rounds 81-140 are v55-current (cyberquincy is stale there —
freeplay cash was buffed a few updates ago, x0.02 -> x0.04 past round 120).
"""

from __future__ import annotations

import functools

import pytest

from services.btd6_data_service import get_dataset, get_round, round_cash

# Medium standard starting cash — the cumulative-cash baseline.
_STARTING_CASH = 650


def _pop_size_table() -> dict[str, int]:
    """Total pops to fully clear one bloon of each type (1 + its children)."""
    bloons = {b.id: b for b in get_dataset().bloons}

    @functools.lru_cache(maxsize=None)
    def pop_size(bid: str) -> int:
        total = 1
        for child in bloons[bid].children_list:
            total += int(child["count"]) * pop_size(str(child["bloon_id"]))
        return total

    return {bid: pop_size(bid) for bid in bloons}


def _cash_per_pop(n: int) -> float:
    """v55 ``DefaultIncomeSet`` cash-per-pop multiplier for round ``n``."""
    if n <= 50:
        return 1.0
    if n <= 60:
        return 0.5
    if n <= 85:
        return 0.2
    if n <= 100:
        return 0.1
    if n <= 120:
        return 0.05
    return 0.04  # 121-140 (current; the old value was 0.02)


def test_stored_round_cash_matches_recomputed_from_composition():
    pop = _pop_size_table()
    for r in get_dataset().rounds:
        pop_count = sum(int(g["count"]) * pop[str(g["bloon_id"])] for g in r.groups)
        expected = round(
            pop_count * _cash_per_pop(r.round_number) + (100 + r.round_number),
            2,
        )
        assert r.cash is not None, f"round {r.round_number} is missing a cash value"
        assert r.cash == expected, (
            f"round {r.round_number}: stored cash={r.cash} but the composition "
            f"({pop_count} pops x {_cash_per_pop(r.round_number)} + "
            f"{100 + r.round_number}) implies {expected}"
        )


def test_cumulative_cash_is_running_total_from_medium_start():
    cumulative = float(_STARTING_CASH)
    for r in get_dataset().rounds:
        cumulative = round(cumulative + r.cash, 2)
        assert r.cumulative_cash == cumulative, (
            f"round {r.round_number}: stored cumulative {r.cumulative_cash} != "
            f"running total {cumulative}"
        )


def test_known_round_cash_anchors():
    by_n = {r.round_number: r for r in get_dataset().rounds}
    # Round 1: 20 Reds x $1/pop + ($100 + 1) end bonus = $121 (validated vs cq).
    assert by_n[1].cash == 121 and by_n[1].cumulative_cash == 771
    # Round 80 (the cyberquincy anchor): 0.2 cash/pop band.
    assert by_n[80].cash == 1400.2
    # Round 140 uses the *current* v55 freeplay decay (x0.04), not the old x0.02.
    assert by_n[140].cash == 1307.68


# ---------------------------------------------------------------------------
# round_cash() — the deterministic round / inclusive-range cash query.
#
# Phase 1A of the AI + BTD6 answerability roadmap
# (docs/planning/ai-btd6-answerability-roadmap-2026-06-09.md): the BTD6 data
# owner derives the range total so a chat answer never depends on the model
# doing arithmetic over context facts. These pin the *semantics* of every row
# in the roadmap's Phase 1A behaviour table.
# ---------------------------------------------------------------------------


def _cash(n: int) -> float:
    entry = get_round(n)
    assert entry is not None and entry.cash is not None
    return float(entry.cash)


def _cumulative(n: int) -> float:
    entry = get_round(n)
    assert entry is not None and entry.cumulative_cash is not None
    return float(entry.cumulative_cash)


def test_round_cash_single_round_returns_round_and_cumulative():
    res = round_cash(1)
    assert res["found"] is True
    assert res["single_round"] is True
    assert res["round_start"] == res["round_end"] == 1
    assert res["round_cash"] == 121
    assert res["cumulative_cash"] == 771
    assert res["roundset"] == "default"
    assert res["starting_cash"] == 650.0


def test_round_cash_single_via_equal_endpoints_matches_single_form():
    # A range with equal endpoints is the single-round case, byte-identical.
    assert round_cash(80, 80) == round_cash(80)


def test_round_cash_inclusive_range_counts_both_endpoints():
    res = round_cash(50, 60)
    assert res["found"] is True
    assert res["single_round"] is False
    assert res["inclusive"] is True
    assert res["normalized"] is False
    assert (res["round_start"], res["round_end"]) == (50, 60)
    assert res["rounds_counted"] == 11
    # Owner total = sum of cash for rounds 50..60 *inclusive of both endpoints*.
    inclusive = round(sum(_cash(n) for n in range(50, 61)), 2)
    assert res["range_cash"] == inclusive
    # It must NOT equal the exclusive reading cumulative(60) - cumulative(50),
    # which silently drops round 50's cash — the exact ambiguity this query kills.
    exclusive = round(_cumulative(60) - _cumulative(50), 2)
    assert res["range_cash"] != exclusive
    assert inclusive - exclusive == pytest.approx(_cash(50))


@pytest.mark.parametrize("lo,hi", [(50, 60), (1, 10), (7, 8), (100, 140), (33, 99)])
def test_round_cash_range_exposes_cumulative_identity(lo, hi):
    # The published fields must satisfy range_cash == cumulative(B) - cumulative(A-1),
    # so the result is self-auditable rather than a bare number.
    res = round_cash(lo, hi)
    assert res["found"] is True
    delta = round(res["cumulative_at_end"] - res["cumulative_before_start"], 2)
    assert res["range_cash"] == pytest.approx(delta)


def test_round_cash_range_from_round_one_uses_starting_cash_baseline():
    res = round_cash(1, 10)
    # No round 0 exists; the baseline before round 1 is the Medium $650 start.
    assert res["cumulative_before_start"] == 650.0
    assert res["range_cash"] == pytest.approx(round(_cumulative(10) - 650.0, 2))


def test_round_cash_reversed_range_is_normalized():
    forward = round_cash(50, 60)
    reversed_ = round_cash(60, 50)
    assert reversed_["normalized"] is True
    assert forward["normalized"] is False
    assert (reversed_["round_start"], reversed_["round_end"]) == (50, 60)
    assert reversed_["range_cash"] == forward["range_cash"]


def test_round_cash_full_range_caps_detail_but_totals_in_full():
    res = round_cash(1, 140)
    assert res["found"] is True
    assert res["rounds_counted"] == 140
    assert res["truncated"] is True
    assert len(res["per_round"]) == 40  # _ROUND_DETAIL_CAP — bounded detail
    # The total is summed over the whole range, never just the capped detail.
    assert res["range_cash"] == pytest.approx(
        round(sum(_cash(n) for n in range(1, 141)), 2)
    )
    assert res["range_cash"] == pytest.approx(round(_cumulative(140) - 650.0, 2))


def test_round_cash_out_of_range_single_is_structured_refusal():
    res = round_cash(200)
    assert res["found"] is False
    assert res["reason"] == "invalid_range"
    # A refusal never carries a fabricated number.
    assert "range_cash" not in res and "round_cash" not in res


@pytest.mark.parametrize("lo,hi", [(0, 0), (-5, -1), (200, 210)])
def test_round_cash_fully_out_of_range_is_invalid(lo, hi):
    res = round_cash(lo, hi)
    assert res["found"] is False
    assert res["reason"] == "invalid_range"


def test_round_cash_partial_overlap_reports_unavailable():
    # 138..145 overlaps the known set (max 140) but extends past it — name the
    # missing rounds rather than returning a partial-range total as if complete.
    res = round_cash(138, 145)
    assert res["found"] is False
    assert res["reason"] == "cash_unavailable"
    assert "141" in res["note"]


def test_round_cash_assumptions_disclose_economy_boundary():
    res = round_cash(50, 60)
    text = res["assumptions"].lower()
    assert "medium" in text
    assert "no income towers" in text
    # The unsupported-modifier boundary is part of the answer, not silent.
    assert "double cash" in text and "half cash" in text
    assert res["roundset"] == "default"
