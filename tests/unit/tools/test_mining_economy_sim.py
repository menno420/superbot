"""Smoke + parity tests for the mining economy balance sim.

The sim (`tools/game_sim/mining_economy_sim.py`) is a disposable design tool, not
runtime code, but it is the source of the numbers in the mining-balance design
doc — so a light guard keeps it runnable, keeps its balance invariants honest,
and (the important half) **pins its mirrored constants to the live game** so the
recommendation can't silently drift from what the bot actually does. Mirrors the
creature-sim parity test (`test_creature_sim_engine_parity.py`); loaded via
importlib (the repo convention for non-package tool scripts).
"""

from __future__ import annotations

import importlib.util
import random
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "tools" / "game_sim" / "mining_economy_sim.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("mining_economy_sim_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# --- Parity: the mirrored constants must match the live game -----------------


def test_ore_value_parity(mod):
    """Sim ore values mirror the live RESOURCE catalog (the coin faucet)."""
    from utils.mining import items

    for ore, value in mod.ORE_VALUE.items():
        assert items.item_value(ore) == value, ore


def test_ore_weight_parity(mod):
    """Sim surface ore weights + depth re-weighting mirror rewards.py."""
    from utils.mining import rewards

    for ore, weight in mod.SURFACE_ORE_WEIGHTS.items():
        assert rewards.ORE_WEIGHTS[ore] == weight, ore
    # depth weighting matches at every band (0..MAX_DEPTH)
    for depth in range(mod.MAX_DEPTH + 1):
        assert mod.ore_weights_for_depth(depth) == rewards.ore_weights_for_depth(
            depth,
        ), depth


def test_tool_multiplier_parity(mod):
    """Sim tool multipliers mirror rewards.mine_multiplier for each tool tier."""
    from utils import equipment
    from utils.mining import rewards

    tier_to_item = {
        "none": None,
        "pickaxe": "pickaxe",
        "iron": "iron pickaxe",
        "gold": "gold pickaxe",
        "diamond": "diamond pickaxe",
    }
    for tier, item in tier_to_item.items():
        equipped = {} if item is None else {equipment.TOOL: item}
        live = rewards.mine_multiplier(equipped, {})
        assert mod.TOOL_MULT[tier] == live, tier


def test_max_depth_parity(mod):
    from utils.mining import world

    assert mod.MAX_DEPTH == world.MAX_DEPTH


def test_current_config_mirrors_live_feature_mix(mod):
    """The CURRENT config's cell feature mix mirrors utils/mining/grid.py."""
    from utils.mining import grid

    cur = mod.CURRENT
    # weights, in the sim's (NORMAL, RICH, BARREN, TREASURE) order
    live_w = {f: w for f, w in grid._FEATURE_WEIGHTS}
    assert cur.feature_weights == (
        live_w[grid.CellFeature.NORMAL],
        live_w[grid.CellFeature.RICH],
        live_w[grid.CellFeature.BARREN],
        live_w[grid.CellFeature.TREASURE],
    )
    assert cur.feature_richness == (
        grid._RICHNESS[grid.CellFeature.NORMAL],
        grid._RICHNESS[grid.CellFeature.RICH],
        grid._RICHNESS[grid.CellFeature.BARREN],
        grid._RICHNESS[grid.CellFeature.TREASURE],
    )
    assert cur.dig_cooldown_s == 0.0  # the live game has no dig cooldown


# --- Diagnosis: the sim must detect the imbalance it was built to find -------


def test_current_faucet_is_over_target(mod):
    """The live faucet over-pays every profile vs the hourly target (the bug)."""
    rng = random.Random(1)
    score = mod.score_config(mod.CURRENT, 3000, rng)
    for r in score.results:
        assert r.coins_per_hour > mod.TARGET_HOUR_HI
    # and the geared/fresh gap is far past the playable bound
    assert score.ratio > mod.MAX_VET_NEWCOMER_RATIO


def test_deeper_pays_more(mod):
    """Deeper bands draw richer ore → higher mean coins/dig (the design intent)."""
    rng = random.Random(2)
    surface = mod.simulate_profile(
        mod.CURRENT,
        mod.Profile("s", "none", 0),
        4000,
        rng,
    )
    magma = mod.simulate_profile(
        mod.CURRENT,
        mod.Profile("m", "none", mod.MAX_DEPTH),
        4000,
        rng,
    )
    assert magma.coins_per_dig > surface.coins_per_dig


# --- Sweep: a balanced config must exist and clear the hard targets ----------


def test_sweep_finds_a_balanced_config(mod):
    scores = mod.sweep(1500, seed=42)
    best = scores[0]
    assert best.penalty < 0.5  # the recommendation satisfies the hard targets
    per_hour = [r.coins_per_hour for r in best.results]
    for ph in per_hour:
        assert mod.TARGET_HOUR_LO * 0.9 <= ph <= mod.TARGET_HOUR_HI * 1.1
    assert best.ratio <= mod.MAX_VET_NEWCOMER_RATIO
    assert (
        mod.TARGET_BONANZA_LO <= best.cfg.bonanza_rate() <= mod.TARGET_BONANZA_HI
    )
    # the recommendation introduces the missing frequency brake
    assert best.cfg.dig_cooldown_s > 0


def test_sweep_is_deterministic(mod):
    a = mod.sweep(1000, seed=7)[0]
    b = mod.sweep(1000, seed=7)[0]
    assert a.cfg.name == b.cfg.name
    assert a.penalty == b.penalty


def test_bonanza_rate_math(mod):
    """RICH+TREASURE share of cells — the 'too frequent' lever."""
    assert mod.CURRENT.bonanza_rate() == pytest.approx(0.25)


def test_main_runs_and_reports(mod, capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["sim", "--trials", "400", "--seed", "1"])
    rc = mod.main()
    out = capsys.readouterr().out
    assert rc == 0
    assert "VERDICT:" in out
    assert "RECOMMENDED" in out
