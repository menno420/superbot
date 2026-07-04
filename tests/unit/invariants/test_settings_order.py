"""Invariant: the shipped settings orders match the simulation's recommendation.

The ordering logic lives in the settings-order simulation
(``tools/sim/settings_order_sim.py``), which reads the LIVE route + subsystem
tables and derives the roots-first routes order. This test pins the shipped
``_ROUTE_DISPLAY_ORDER`` to that recommendation so a future edit to the routes
list (or the fallback DAG) can't silently drift the operator-facing order. The
sim is loaded by file path because ``tools/`` is not an importable package.

(The settings-dropdown ordering is a schema-registry-dependent surface and is
guarded separately by ``tests/unit/views/test_settings_hub_view.py``.)
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SIM_PATH = (
    Path(__file__).resolve().parents[3] / "tools" / "sim" / "settings_order_sim.py"
)


def _load_sim():
    spec = importlib.util.spec_from_file_location("settings_order_sim", _SIM_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def sim():
    return _load_sim()


def test_shipped_route_order_matches_the_recommendation(sim):
    """``check_orders`` returns no drift problems for the shipped order."""
    problems = sim.check_orders()
    assert problems == [], "\n".join(problems)


def test_recommended_route_order_leads_with_the_fallback_roots(sim):
    """The two fallback roots (``mod`` / ``events``) lead the recommendation —
    the property that makes 'set these two and you're covered' true.
    """
    order = sim.recommended_route_order()
    assert order[0] == "mod"
    assert order[1] == "events"
    # And it is a permutation of the live route set (nothing dropped/added).
    from cogs.logging.routes_panel import _ROUTE_DISPLAY_ORDER

    assert set(order) == set(_ROUTE_DISPLAY_ORDER)


def test_roots_first_beats_the_old_category_first_scroll_cost(sim):
    """Scroll-to-full-coverage strictly improves under the recommendation —
    the sim's headline "easy and clear to change all this" metric.
    """
    rec = sim.recommended_route_order()
    alpha = tuple(sorted(sim._ROUTE_TO_BINDING))
    assert sim.scroll_to_full_coverage(rec) < sim.scroll_to_full_coverage(alpha)
    assert sim.scroll_to_full_coverage(rec) <= 1
