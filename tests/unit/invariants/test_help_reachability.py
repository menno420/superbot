"""Invariant — every Help subsystem is reachable from the menu.

After the help-menu regrouping (PR #1290) homed every subsystem under a hub
and the redundant "All Commands / Advanced" browser was removed (PR #1294),
there is no catch-all fallback anymore: a subsystem that is neither a hub host
nor a hub child is **completely unreachable** from `!help`. This invariant
fails CI the moment that happens — the standing guard the removed Advanced
surface used to provide implicitly.

The check logic lives in the grouping simulation
(`tools/sim/help_menu_grouping_sim.py::check_reachability`), which reads the
live registries and mirrors the `cogs/help/panels.py` click model. The module
is loaded by file path because `tools/` is not an importable package.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SIM_PATH = (
    Path(__file__).resolve().parents[3] / "tools" / "sim" / "help_menu_grouping_sim.py"
)


def _load_sim():
    spec = importlib.util.spec_from_file_location(
        "help_menu_grouping_sim",
        _SIM_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before exec: the module's dataclasses resolve their field
    # types via ``sys.modules[cls.__module__]`` at decoration time.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def sim():
    return _load_sim()


def test_every_subsystem_is_reachable_in_help(sim):
    """No orphans, every feature <= 3 clicks, no section overflows the dropdown.

    If this fails, a subsystem was added (or re-parented) without a route into
    the menu. The fix is almost always: give it a ``parent_hub`` pointing at a
    registered hub (and list it in that hub's ``primary_children``).
    """
    violations = sim.check_reachability()
    assert violations == [], "Help reachability invariant violated:\n" + "\n".join(
        f"  - {v}" for v in violations
    )


def test_guard_has_teeth_detects_an_unhomed_subsystem(sim):
    """The guard must actually catch an orphan — a vacuous check is worse than
    none. Simulate a regression by dropping a known child from its section and
    confirm the orphan detector flags exactly it.
    """
    # A scheme that homes nothing flags every subsystem as an orphan.
    empty = sim.Scheme(name="empty", sections=[])
    assert sim.orphans_of(empty), "orphans_of must flag un-homed subsystems"

    # Dropping one child from the live scheme flags exactly that child.
    live = sim.scheme_live()
    target = "blackjack"
    for section in live.sections:
        if target in section.children:
            section.children.remove(target)
            break
    else:  # pragma: no cover - defensive: blackjack should be a Games child
        pytest.fail(f"{target!r} was not a child of any live section")

    assert target in sim.orphans_of(live)
