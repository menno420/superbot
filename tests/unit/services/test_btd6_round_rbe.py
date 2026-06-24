"""Per-round RBE lookup (``round_rbe``) — base and freeplay-scaled.

``round_rbe`` exposes two RBE notions that must stay honest:

* ``base_rbe`` — the wiki Module:BTD6_rounds total at base bloon health.
* ``effective_rbe`` — the same spawn tree recomputed with the freeplay rules
  (MOAB-class HP scaling + superceramic swap), via ``bloon_rbe_at_round``.

The load-bearing invariant is that the effective sum *reconstructs* the stored
base RBE for every round through 80 (no scaling applies there), so the 81+
divergence is provably the freeplay rules and not a methodology mismatch. The
canonical freeplay anchor is BAD @ r100 = 67,200 (vs 55,760 base), the same
value pinned by ``test_btd6_bloon_scaling.py``.

(Bloon *composition* per round is the pre-existing ``round_composition``; this
file only covers the new RBE function. The round embed's composition rendering
is covered by ``tests/unit/cogs/test_btd6_income_rbe_builders.py``.)
"""

from __future__ import annotations

import pytest

from services.btd6_data_service import round_rbe


def test_single_round_base_and_effective_at_the_r100_anchor() -> None:
    res = round_rbe(100)
    assert res["found"] is True
    assert res["single_round"] is True
    assert res["base_rbe"] == 55760
    assert res["effective_rbe"] == 67200  # the verified freeplay anchor
    assert res["scaled"] is True
    # Breakdown names the one bloon and both per-bloon figures.
    assert len(res["breakdown"]) == 1
    row = res["breakdown"][0]
    assert row["bloon"] == "BAD"
    assert row["count"] == 1
    assert row["base_rbe_each"] == 55760
    assert row["effective_rbe_each"] == 67200


def test_single_round_below_freeplay_is_not_scaled() -> None:
    res = round_rbe(6)
    assert res["scaled"] is False
    assert res["base_rbe"] == res["effective_rbe"]


def test_effective_reconstructs_base_through_round_80() -> None:
    # The methodology proof: with no freeplay scaling (rounds <= 80), summing
    # each group's count x bloon_rbe_at_round must equal the stored base RBE.
    for n in range(1, 81):
        res = round_rbe(n)
        if res.get("base_rbe") is None:
            continue
        assert (
            res["effective_rbe"] == res["base_rbe"]
        ), f"round {n} diverged below freeplay"
        assert res["scaled"] is False, f"round {n} should not be scaled"


def test_freeplay_rounds_diverge_from_base() -> None:
    # Superceramic swap can lower RBE (r81), MOAB scaling raises it (r140).
    assert round_rbe(81)["effective_rbe"] < round_rbe(81)["base_rbe"]
    assert round_rbe(140)["effective_rbe"] > round_rbe(140)["base_rbe"]


def test_range_totals_and_rows() -> None:
    res = round_rbe(100, 120)
    assert res["found"] is True
    assert res["single_round"] is False
    assert res["rounds_counted"] == 21
    assert len(res["per_round"]) == 21
    assert res["scaled"] is True
    # Totals equal the sum of the per-round rows we expose.
    assert res["base_rbe_total"] == sum(r["base_rbe"] for r in res["per_round"])
    assert res["effective_rbe_total"] == sum(
        r["effective_rbe"] for r in res["per_round"]
    )
    # Effective beats base once blimps scale.
    assert res["effective_rbe_total"] > res["base_rbe_total"]


def test_range_normalizes_reversed_endpoints() -> None:
    res = round_rbe(120, 100)
    assert res["normalized"] is True
    assert res["round_start"] == 100
    assert res["round_end"] == 120


@pytest.mark.parametrize(
    ("start", "end", "reason"),
    [
        (200, 250, "invalid_range"),
        (100, 200, "rbe_unavailable"),  # straddles the edge of the known set
    ],
)
def test_out_of_range_fails_closed(start: int, end: int, reason: str) -> None:
    res = round_rbe(start, end)
    assert res["found"] is False
    assert res["reason"] == reason


def test_unknown_roundset_fails_closed() -> None:
    res = round_rbe(1, 10, roundset="nonsense")
    assert res["found"] is False
    assert res["reason"] == "unknown_roundset"
