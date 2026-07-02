"""Tests for the retention-policy simulator (Lane B5).

Covers determinism under a fixed seed, the hard feasibility constraint
(delete_bare excluded when it violates the miss bound), the sensitivity
sweep, the default-calibration round trip through the full search, the
WHY-IT-WON record, the tombstone-vs-bare miss ordering, and the grid
construction (class declarations + the grid_scale widening knob).
"""

from engine.economy.simulator import (
    RETENTION_MODES,
    calibration_recipe,
    default_calibration,
    policy_grid,
    run_search,
    simulate_policy,
)


def _small_cal() -> dict:
    """One-class calibration with a tiny grid — fast and easy to reason about."""
    cal = default_calibration()
    cal["classes"] = [
        {
            "name": "logs",
            "birth_rate": 1.0,
            "words_each": 500.0,
            "initial_files": 100.0,
            "cited_frac": 0.0,
            "cascade_unlock_frac": 0.0,
            "backref_rate": 0.5,  # high demand: bare deletion must be infeasible
            "tombstone_lines_each": 0.0,
            "indexed": False,
            "active_pool": None,
            "modes": ["keep", "delete_tomb", "delete_bare"],
            "windows": [1, 2],
        },
    ]
    cal["journal_caps"] = [2000]
    cal["sensitivity_keys"] = ["stale_act_base", "classes.logs.backref_rate"]
    return cal


def _policy(cal: dict, mode: str, window: int) -> dict:
    """Build one hand-crafted policy applying (mode, window) to every class."""
    return {
        "classes": {
            c["name"]: {"mode": mode, "window": window} for c in cal["classes"]
        },
        "ledger_compress": True,
        "journal_cap": 2000.0,
        "index_hist_tombstones": True,
    }


# ---------------------------------------------------------------------------
# determinism
# ---------------------------------------------------------------------------


def test_run_search_deterministic_same_seed():
    cal = _small_cal()
    first = run_search(cal, bands=8, seed=7)
    second = run_search(cal, bands=8, seed=7)
    assert first["winner"]["name"] == second["winner"]["name"]
    assert first["winner"]["total"] == second["winner"]["total"]
    assert first["feasible_count"] == second["feasible_count"]
    assert first["sensitivity"] == second["sensitivity"]
    assert first["why_it_won"] == second["why_it_won"]


def test_simulate_policy_deterministic_same_seed():
    cal = _small_cal()
    pol = _policy(cal, "delete_tomb", 2)
    assert simulate_policy(pol, cal, bands=6, seed=3) == simulate_policy(
        pol,
        cal,
        bands=6,
        seed=3,
    )


# ---------------------------------------------------------------------------
# feasibility constraint
# ---------------------------------------------------------------------------


def test_feasibility_excludes_bare_delete_under_high_backref():
    cal = _small_cal()  # backref_rate 0.5 -> bare miss far above the 0.005 bound
    bare = simulate_policy(_policy(cal, "delete_bare", 1), cal, bands=8)
    assert bare["miss_per_band"] > cal["miss_per_band_max"]
    assert bare["feasible"] is False
    result = run_search(cal, bands=8)
    grid = policy_grid(cal)
    assert result["feasible_count"] < len(grid)  # something was excluded
    assert result["feasible_count"] > 0  # keep/tomb candidates survive
    winner_modes = {
        spec["mode"] for spec in result["winner"]["policy"]["classes"].values()
    }
    assert "delete_bare" not in winner_modes


def test_keep_everything_always_feasible():
    cal = _small_cal()
    keep = simulate_policy(_policy(cal, "keep", 0), cal, bands=8)
    assert keep["miss_per_band"] == 0.0
    assert keep["feasible"] is True


# ---------------------------------------------------------------------------
# tombstone vs bare miss ordering
# ---------------------------------------------------------------------------


def test_delete_tomb_never_worse_miss_than_delete_bare():
    cal = _small_cal()
    for window in (1, 2, 4):
        tomb = simulate_policy(_policy(cal, "delete_tomb", window), cal, bands=8)
        bare = simulate_policy(_policy(cal, "delete_bare", window), cal, bands=8)
        assert tomb["miss_per_band"] <= bare["miss_per_band"]
        assert bare["miss_per_band"] > 0.0  # the comparison is not vacuous


# ---------------------------------------------------------------------------
# sensitivity sweep
# ---------------------------------------------------------------------------


def test_sensitivity_sweep_returns_entries():
    cal = _small_cal()
    result = run_search(cal, bands=8)
    entries = result["sensitivity"]
    expected = len(cal["sensitivity_keys"]) * len(cal["sensitivity_multipliers"])
    assert len(entries) == expected
    for entry in entries:
        assert entry["key"] in cal["sensitivity_keys"]
        assert entry["multiplier"] in (1 / 3, 3)
        assert entry["total"] > 0
        assert entry["delta"] == entry["total"] - result["winner"]["total"]


# ---------------------------------------------------------------------------
# default calibration round trip + why-it-won
# ---------------------------------------------------------------------------


def test_default_calibration_round_trips_through_run_search():
    result = run_search(default_calibration())
    assert set(result) == {"winner", "why_it_won", "feasible_count", "sensitivity"}
    winner = result["winner"]
    assert winner["feasible"] is True
    assert result["feasible_count"] >= 1
    assert winner["total"] > 0
    for component in ("boot", "discovery", "backref", "stale"):
        assert winner[component] >= 0
    assert winner["total"] == sum(
        winner[c] for c in ("boot", "discovery", "backref", "stale")
    )
    assert result["sensitivity"]


def test_why_it_won_present_and_names_winner():
    result = run_search(_small_cal(), bands=8)
    why = result["why_it_won"]
    assert why
    assert result["winner"]["name"] in why
    assert "words/session" in why
    assert "retrieval-miss" in why


# ---------------------------------------------------------------------------
# grid construction
# ---------------------------------------------------------------------------


def test_policy_grid_built_from_class_declarations():
    cal = _small_cal()
    grid = policy_grid(cal)
    # keep collapses to one candidate; tomb/bare get both windows:
    # (1 + 2 + 2) class combos x 2 ledger toggles x 1 journal cap = 10
    assert len(grid) == 10
    assert len({p["name"] for p in grid}) == len(grid)  # names unique
    for policy in grid:
        spec = policy["classes"]["logs"]
        assert spec["mode"] in RETENTION_MODES
        if spec["mode"] == "keep":
            assert spec["window"] == 0
        else:
            assert spec["window"] in (1, 2)


def test_grid_scale_widens_candidate_windows():
    cal = _small_cal()
    base = len(policy_grid(cal))
    cal["grid_scale"] = 2  # windows {1, 2} widen to {1, 2, 4}
    widened = policy_grid(cal)
    assert len(widened) > base
    windows = {
        p["classes"]["logs"]["window"]
        for p in widened
        if p["classes"]["logs"]["mode"] != "keep"
    }
    assert windows == {1, 2, 4}


# ---------------------------------------------------------------------------
# calibration recipe
# ---------------------------------------------------------------------------


def test_calibration_recipe_is_a_generic_shell_block():
    recipe = calibration_recipe()
    assert "```sh" in recipe
    assert "wc -w" in recipe  # boot word count
    assert "git log" in recipe  # velocity measurement
    assert "grep" in recipe  # noise profile + back-reference greps
    assert "UNVERIFIED" in recipe  # the kit ships the search, not constants
    assert "sensitivity_keys" in recipe  # sweep discipline documented
