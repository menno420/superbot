"""Smoke + invariant tests for the creature-battle playability sim.

The sim (`tools/game_sim/creature_battle_sim.py`) is a disposable design tool,
not runtime code, but it is the source of the numbers in the creature-game
design doc — so a light guard keeps it runnable and keeps its core fairness
invariants honest (the engine must be unbiased; the type chart must be
symmetric). Loaded via importlib (the repo convention for non-package tool
scripts — mirrors `tests/unit/scripts/test_export_dashboard_data.py`).
"""

from __future__ import annotations

import importlib.util
import random
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "tools" / "game_sim" / "creature_battle_sim.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("creature_battle_sim_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_type_chart_is_symmetric(mod):
    """Each element beats exactly 2, loses to 2, neutral to 1 (incl. self)."""
    for el in mod.ELEMENTS:
        mults = [mod.effectiveness(el, other) for other in mod.ELEMENTS]
        assert mults.count(mod.STRONG_MULT) == 2
        assert mults.count(mod.WEAK_MULT) == 2
        # neutral covers the +3 opposite AND the mirror (self) → 2 here
        assert mults.count(mod.NEUTRAL_MULT) == 2


def test_roster_well_formed(mod):
    assert len(mod.ROSTER) == 12
    assert {s.element for s in mod.ROSTER} == set(mod.ELEMENTS)
    for s in mod.ROSTER:
        # budget spread rounds, so allow ±2 of the rarity budget
        assert abs(s.budget - mod.RARITY_BUDGET[s.rarity]) <= 2


def test_engine_is_unbiased_at_equal_level(mod):
    """Normalized PvP fairness — the core non-P2W invariant (team A ≈ 50%)."""
    rng = random.Random(123)
    wr = mod.sim_normalized_fairness(rng, 800)
    assert 0.43 <= wr <= 0.57


def test_higher_level_wins_more_in_raw_mode(mod):
    """The motivating finding: raw level dominance is real (monotone, steep)."""
    rng = random.Random(7)
    lf = dict(mod.sim_level_fairness(rng, 400))
    assert lf[0] < 0.6  # even mirror is a coin-flip-ish
    assert lf[6] > 0.9  # a real gap dominates → why PvP normalizes levels


def test_catch_grind_is_a_sitting_not_a_slog(mod):
    rng = random.Random(99)
    cg = mod.sim_catch_grind(rng, 400)
    assert cg[1] <= 14  # fresh player reaches a team of 3 quickly


def test_main_runs_and_reports(mod, capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["sim", "--trials", "200", "--seed", "1"])
    rc = mod.main()
    out = capsys.readouterr().out
    assert rc == 0
    assert "VERDICT:" in out
