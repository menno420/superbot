"""Unit tests for the pure Paragon power model and reverse solver.

These pin the formula (validated field-by-field against the live Paragon
Calculator API) and the non-degenerate behaviour of the reverse solver.
No network — this module is stdlib-only.
"""

from __future__ import annotations

from utils.btd6 import paragon_math as pm
from utils.btd6.paragon_math import ParagonInputs, SolveStrategy

_DART = "apex_plasma_master"


# --- thresholds --------------------------------------------------------------


def test_threshold_anchors_and_monotonic():
    assert pm.threshold(1) == 1693
    assert pm.threshold(100) == 200_000
    assert all(pm.threshold(d) < pm.threshold(d + 1) for d in range(1, 100))


def test_degree_from_power_round_trips_every_degree():
    for degree in range(1, 101):
        assert pm.degree_from_power(pm.threshold(degree)) == degree
        if degree > 1:
            assert pm.degree_from_power(pm.threshold(degree) - 1) == degree - 1


def test_degree_floor_is_one_even_at_zero_power():
    assert pm.degree_from_power(0) == 1
    assert pm.power_for_next_degree(0) == pm.threshold(2)


def test_power_for_next_degree_is_zero_at_max():
    assert pm.power_for_next_degree(pm.TOTAL_POWER_FOR_MAX_DEGREE) == 0
    assert pm.next_degree(pm.TOTAL_POWER_FOR_MAX_DEGREE) == 100


# --- forward replica (validated against the live API) ------------------------


def _dart_bp() -> int:
    return pm.base_price(pm.resolve_paragon(_DART), "medium")


def test_forward_matches_validated_api_example():
    bd = pm.compute_breakdown(
        ParagonInputs(
            tower=_DART,
            pops=8_000_000,
            cash_spent=150_000,
            upgrade_count=60,
            tier5_count=1,
            geraldo_totems=5,
        ),
        _dart_bp(),
    )
    assert (
        bd.pops.power,
        bd.upgrades.power,
        bd.cash.power,
        bd.extra_t5s.power,
        bd.totems.power,
    ) == (
        44444,
        6000,
        20000,
        6000,
        10000,
    )
    assert bd.total_power == 86444
    assert bd.degree == 68


def test_total_power_is_reported_raw_while_degree_caps_at_100():
    # Totems are uncapped: total_power exceeds 200k but degree is pinned to 100.
    bd = pm.compute_breakdown(
        ParagonInputs(
            tower=_DART,
            pops=99_999_999,
            upgrade_count=250,
            tier5_count=1,
            geraldo_totems=100,
        ),
        _dart_bp(),
    )
    assert bd.total_power == 306000
    assert bd.degree == 100


def test_axis_caps_enforced():
    bd = pm.compute_breakdown(
        ParagonInputs(
            tower=_DART,
            pops=10**9,
            upgrade_count=10_000,
            cash_spent=10**9,
            tier5_count=99,
        ),
        _dart_bp(),
    )
    assert bd.pops.power == pm.POPS_POWER_CAP and bd.pops.capped
    assert bd.upgrades.power == pm.UPGRADES_POWER_CAP and bd.upgrades.capped
    assert bd.cash.power == pm.CASH_POWER_CAP and bd.cash.capped
    assert bd.extra_t5s.power == pm.T5_POWER_CAP and bd.extra_t5s.capped
    assert bd.totems.max_power is None and bd.totems.capped is False


def test_income_counts_as_four_pops():
    bd = pm.compute_breakdown(ParagonInputs(tower=_DART, income=45), _dart_bp())
    # 45 income * 4 = 180 pops -> exactly 1 power.
    assert bd.pops.power == 1


def test_slider_cash_has_five_percent_premium():
    bp = _dart_bp()
    spent = pm.compute_breakdown(
        ParagonInputs(tower=_DART, cash_spent=15000), bp
    ).cash.power
    slider = pm.compute_breakdown(
        ParagonInputs(tower=_DART, slider_cash=15000), bp
    ).cash.power
    assert slider < spent  # the slider is 95% efficient


# --- resolver ----------------------------------------------------------------


def test_resolver_matches_id_name_tower_and_aliases():
    for text in [
        "apex_plasma_master",
        "Apex Plasma Master",
        "Dart Monkey",
        "dart",
        "bucc",
        "boat paragon",
        "B.O.M.B.",
        "sub",
        "druid",
        "spike factory",
        "ICE monkey",
    ]:
        assert pm.resolve_paragon(text) is not None, text
    assert pm.resolve_paragon("not a tower") is None
    assert pm.resolve_paragon("") is None


def test_catalogue_has_thirteen_paragons_with_base_prices():
    assert len(pm.PARAGONS) == 13
    assert all(p.base_price_medium > 0 for p in pm.PARAGONS)
    assert pm.BASE_PRICES_MEDIUM["apex_plasma_master"] == 150_000


# --- validation warnings -----------------------------------------------------


def test_validate_warns_on_solo_non_dart_extra_t5():
    warnings = pm.validate_inputs(
        ParagonInputs(tower="Monkey Sub", tier5_count=1, player_count=1)
    )
    assert any(w.type == "extra_t5_ignored" for w in warnings)


def test_validate_clamps_coop_extra_t5():
    warnings = pm.validate_inputs(
        ParagonInputs(tower="Monkey Sub", tier5_count=20, player_count=4)
    )
    assert any(w.type == "extra_t5_clamped" for w in warnings)


def test_validate_flags_upgrade_overflow_and_unknown_tower():
    assert any(
        w.type == "upgrades_capped"
        for w in pm.validate_inputs(ParagonInputs(tower=_DART, upgrade_count=200))
    )
    assert any(
        w.type == "unknown_tower"
        for w in pm.validate_inputs(ParagonInputs(tower="zzz"))
    )


# --- T5 limits ---------------------------------------------------------------


def test_t5_limits_by_mode_and_paragon():
    assert pm.max_extra_t5_count("solo", is_dart=True) == 1
    assert pm.max_extra_t5_count("solo", is_dart=False) == 0
    assert pm.max_extra_t5_count("coop", is_dart=False) == 9
    assert pm.game_mode_for(1) == "solo"
    assert pm.game_mode_for(3) == "coop"


# --- reverse solver ----------------------------------------------------------


def test_every_strategy_reaches_the_target_degree():
    for paragon in pm.PARAGONS:
        for player_count in (1, 4):
            for strategy in SolveStrategy:
                for target in (1, 25, 50, 75, 90, 95, 100):
                    sol = pm.solve_requirements(
                        paragon,
                        target,
                        strategy,
                        player_count=player_count,
                        difficulty="medium",
                    )
                    assert sol.breakdown.degree >= target, (
                        paragon.paragon_id,
                        player_count,
                        strategy.value,
                        target,
                        sol.breakdown.degree,
                    )


def test_least_cash_minimises_cash_versus_balanced():
    dart = pm.resolve_paragon(_DART)
    least = pm.solve_requirements(dart, 60, SolveStrategy.LEAST_CASH, player_count=1)
    balanced = pm.solve_requirements(dart, 60, SolveStrategy.BALANCED, player_count=1)
    assert least.inputs.cash_spent <= balanced.inputs.cash_spent
    # A mid degree is reachable without cash by leaning on pops.
    assert least.inputs.cash_spent == 0


def test_least_tiers_and_least_pops_minimise_their_axis():
    dart = pm.resolve_paragon(_DART)
    least_tiers = pm.solve_requirements(
        dart, 60, SolveStrategy.LEAST_TIERS, player_count=1
    )
    least_pops = pm.solve_requirements(
        dart, 60, SolveStrategy.LEAST_POPS, player_count=1
    )
    balanced = pm.solve_requirements(dart, 60, SolveStrategy.BALANCED, player_count=1)
    assert least_tiers.inputs.upgrade_count <= balanced.inputs.upgrade_count
    assert least_pops.inputs.pops <= balanced.inputs.pops


def test_solo_non_dart_degree_100_needs_twenty_totems():
    # The API reference's own tip: maxing the capped sources leaves a 40k gap.
    sub = pm.resolve_paragon("Monkey Sub")
    sol = pm.solve_requirements(sub, 100, SolveStrategy.LEAST_CASH, player_count=1)
    assert sol.inputs.geraldo_totems == 20
    assert sol.requires_totems is True


def test_coop_reaches_degree_100_without_totems():
    # Co-op T5 capacity (up to 9) covers the gap, so no totems are required.
    sub = pm.resolve_paragon("Monkey Sub")
    sol = pm.solve_requirements(sub, 100, SolveStrategy.BALANCED, player_count=4)
    assert sol.breakdown.degree == 100
    assert sol.inputs.geraldo_totems == 0
