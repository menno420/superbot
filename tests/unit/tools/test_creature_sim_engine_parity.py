"""Parity guard — the creature sim and the runtime battle engine must agree.

The runtime PvP battle engine (``disbot/utils/creatures/battle.py``, PR #1213)
**graduated** its combat math from the disposable playability simulator
(``tools/game_sim/creature_battle_sim.py``). Graduation copies the math rather than
importing it — correctly, because the sim is a *design tool* that must never become
a runtime dependency. The cost of that copy is a **two-sources-of-truth drift
class**: the owner tunes a number in the sim to fix balance, the runtime engine
keeps the old value, and the sim's "PLAYABLE" verdict silently stops describing what
players actually play.

This guard closes that gap. It loads both modules and asserts they agree on every
**shared design constant**. A tuning change to either side that isn't mirrored fails
CI with a clear "sim and engine disagree on X" message. Same shape as the
``panel_base_class`` allowlist↔arch-frozenset parity test (PR #1166).

The sim is loaded via :mod:`importlib` (the repo convention for non-package tool
scripts — mirrors ``tests/unit/tools/test_creature_battle_sim.py``). The engine is a
normal package import.

Provenance + reliability (Q-0105): added 2026-06-21 (the PR #1213 Q-0089 idea,
``docs/ideas/creature-sim-engine-constant-parity-guard-2026-06-21.md``). Disposable:
delete it if the sim is ever retired — at that point the engine is the sole source
of truth and there is nothing left to compare (the sim's own header says it is
deletable once its numbers are pinned into the real subsystem).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from utils.creatures import battle as engine

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "tools" / "game_sim" / "creature_battle_sim.py"


@pytest.fixture(scope="module")
def sim():
    spec = importlib.util.spec_from_file_location(
        "creature_battle_sim_parity_ut", _SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------- type chart


def test_element_cycle_matches(sim) -> None:
    """The engine's canonical ELEMENT_CYCLE is the sim's ELEMENTS tuple (same order)."""
    assert engine.ELEMENT_CYCLE == sim.ELEMENTS


def test_type_multipliers_match(sim) -> None:
    assert engine.STRONG_MULT == sim.STRONG_MULT
    assert engine.WEAK_MULT == sim.WEAK_MULT
    assert engine.NEUTRAL_MULT == sim.NEUTRAL_MULT
    assert engine.NORMAL_TYPE == sim.NORMAL_TYPE


def test_effectiveness_agrees_for_every_pair(sim) -> None:
    """The whole type chart agrees — including Normal and every element ordering.

    The strongest form of parity: not just the constants but the *function output*
    for every (attacker, defender) pair, so a refactor that changes representation
    but not behavior still passes, and a re-wired cycle fails.
    """
    types = (engine.NORMAL_TYPE, *engine.ELEMENT_CYCLE)
    for atk in types:
        for dfd in engine.ELEMENT_CYCLE:
            assert engine.effectiveness(atk, dfd) == sim.effectiveness(atk, dfd), (
                atk,
                dfd,
            )


# --------------------------------------------------------------------------- stats


def test_rarity_budget_matches(sim) -> None:
    assert engine.RARITY_BUDGET == sim.RARITY_BUDGET


def test_archetype_weights_match(sim) -> None:
    assert engine.ARCHETYPE_WEIGHTS == sim.ARCHETYPE_WEIGHTS


def test_level_scaling_rates_match(sim) -> None:
    assert engine.HP_PER_LVL == sim.HP_PER_LVL
    assert engine.OFF_PER_LVL == sim.OFF_PER_LVL


# --------------------------------------------------------------------------- moves


def test_move_powers_and_buffs_match(sim) -> None:
    assert engine.NORMAL_POWER == sim.NORMAL_POWER
    assert engine.ELEMENT_POWER == sim.ELEMENT_POWER
    assert engine.BUFF_STEP == sim.BUFF_STEP
    assert engine.BUFF_CAP == sim.BUFF_CAP


def test_team_size_matches(sim) -> None:
    assert engine.TEAM_SIZE == sim.TEAM_SIZE


def test_signature_move_names_match(sim) -> None:
    """The per-element signature-move display names are identical (no Pokémon IP)."""
    assert engine.ELEMENT_MOVE_NAME == sim._ELEMENT_MOVE


def test_derived_stats_agree_for_the_whole_catalog(sim) -> None:
    """End-to-end: the engine derives the same HP/ATK/DEF/SPD the sim does.

    The sim derives stats inside ``_roster`` (rarity budget split by archetype
    weights); the engine derives them in ``derive_stats``. Walk the live catalog and
    assert they produce identical stat lines for every creature — the behavioral
    proof that the budget + weight + rounding pipeline is shared, not just the
    constants feeding it.
    """
    sim_by_name = {s.name: s for s in sim.ROSTER}
    from utils.creatures.creature import CREATURES

    checked = 0
    for creature in CREATURES:
        species = sim_by_name.get(creature.name)
        if species is None:
            continue  # roster/catalog drift is its own test's concern, not this one
        stats = engine.derive_stats(creature)
        assert (stats.hp, stats.atk, stats.df, stats.spd) == (
            species.hp,
            species.atk,
            species.df,
            species.spd,
        ), creature.name
        checked += 1
    assert (
        checked > 0
    ), "no overlap between engine catalog and sim roster — guard is inert"
