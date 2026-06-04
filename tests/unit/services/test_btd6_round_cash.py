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

from services.btd6_data_service import get_dataset

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
