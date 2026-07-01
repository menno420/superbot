"""Guards for the role-menu builder layout sim (`tools/sim/role_menu_layout_sim.py`).

A disposable advisory tool, so the guard is light: keep it runnable + deterministic,
keep its cost model oriented the right way, and — the important half — **pin its
button inventory to the live builder** so the recommendation can't silently drift
from the real ``RoleMenuBuilder`` surface. Loaded via importlib (repo convention
for non-package tool scripts).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO / "tools" / "sim" / "role_menu_layout_sim.py"
_BUILDER = _REPO / "disbot" / "views" / "roles" / "role_menu_builder.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("role_menu_layout_sim_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_inventory_matches_the_live_builder(mod):
    """Every button the sim models must still exist in RoleMenuBuilder — if a
    button is renamed/removed, this flags the sim as stale (update or delete it).
    """
    source = _BUILDER.read_text(encoding="utf-8")
    for btn in mod.BUTTONS:
        word = btn.label.split()[-1]  # emoji-tolerant: match the text token
        assert word in source, f"sim button {btn.key!r} ({word!r}) not in the builder"
    # 14 is the count the layout question was asked about; a drift here is a signal.
    assert len(mod.BUTTONS) == 14


def test_current_layout_is_well_formed(mod):
    flat = [k for row in mod.CURRENT_LAYOUT for k in row]
    assert set(flat) == {b.key for b in mod.BUTTONS}  # covers exactly the inventory
    assert len(flat) == len(set(flat))  # no duplicates
    assert mod.valid(mod.CURRENT_LAYOUT)  # <=5/row, <=5 rows


def test_journey_weights_sum_to_one(mod):
    assert abs(sum(j.weight for j in mod.JOURNEYS) - 1.0) < 1e-9


def test_optimiser_is_deterministic(mod):
    base = mod.VARIANTS[0]
    a = mod.optimise(base, seed=3, iters=800)
    b = mod.optimise(base, seed=3, iters=800)
    assert a[1] == pytest.approx(b[1])  # same seed -> same best cost


def test_optimiser_beats_the_current_layout(mod):
    base = mod.VARIANTS[0]
    _layout, best = mod.optimise(base, seed=1, iters=2000)
    current = mod.total_cost(base, mod.CURRENT_LAYOUT)
    assert best < current  # the search actually finds something better


def test_cost_model_rewards_hot_buttons_top_left(mod):
    """Sanity: putting a frequently-pressed button (Template) top-left costs less
    than burying it bottom-right — i.e. the cost model points the right way.
    """
    base = mod.VARIANTS[0]
    others = [b.key for b in mod.BUTTONS if b.key != "template"]
    top_left = [["template"] + others[:4], others[4:9], others[9:]]
    bottom_right = [others[:5], others[5:10], others[10:] + ["template"]]
    assert mod.total_cost(base, top_left) < mod.total_cost(base, bottom_right)


def test_lean_advanced_variant_folds_the_rare_knobs(mod):
    lean = next(v for v in mod.VARIANTS if v.name == "lean_advanced")
    # The rarely-tapped knobs are hidden behind one grid button …
    for folded in ("theme", "card", "counts", "mode", "limit"):
        assert lean.grid_key(folded) == "advanced"
    # … but Style is pinned first-screen (owner directive) — never folded …
    assert lean.grid_key("style") == "style"
    # … and the hot content buttons stay top-level too.
    for hot in ("template", "packs", "roles", "post"):
        assert lean.grid_key(hot) == hot


def test_pinned_style_stays_on_the_first_screen(mod):
    """Every optimised variant must place Style on row 0 (owner directive)."""
    assert "style" in mod.PINNED_FIRST_SCREEN
    for v in mod.VARIANTS:
        layout, _cost = mod.optimise(v, seed=1, iters=1500)
        pos = mod.positions(layout)
        assert pos["style"][0] == 0, f"{v.name}: Style not on row 0 ({pos['style']})"
