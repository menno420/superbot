"""Smoke + contract tests for ``scripts/settings_lane_matrix.py``.

The matrix is the machine-readable settings/bindings/provisioning inventory the
P0-3 plan + parity invariants build on.  These tests pin the shape and the
pointer-lane classification logic so the tool stays trustworthy (Q-0105).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "settings_lane_matrix.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("settings_lane_matrix", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["settings_lane_matrix"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def matrix_mod():
    return _load_module()


def test_classify_pointer_dispositions(matrix_mod):
    """The pointer classifier matches the documented three dispositions."""
    classify = matrix_mod._classify_pointer
    assert classify("migrated", True) == "binding_backed_convergeable"
    assert classify("migrated", False) == "binding_backed_deferred"
    assert classify("deferred", False) == "binding_backed_deferred"
    assert classify("none", False) == "orphan_no_binding"


def test_build_matrix_has_expected_shape(matrix_mod):
    """``build_matrix`` returns a populated, internally-consistent inventory."""
    m = matrix_mod.build_matrix()
    # Non-trivial inventory.
    assert m.counts["settings"] > 0
    assert m.counts["bindings"] > 0
    # Counts agree with the row lists.
    assert m.counts["settings"] == len(m.settings)
    assert m.counts["bindings"] == len(m.bindings)
    assert m.counts["pointer_settings"] == len(m.pointers)
    # Pointer sub-counts partition the pointer rows.
    assert (
        m.counts["pointer_convergeable"]
        + m.counts["pointer_deferred"]
        + m.counts["pointer_orphan"]
        == m.counts["pointer_settings"]
    )


def test_known_pointers_are_classified_correctly(matrix_mod):
    """Spot-check the headline pointer dispositions against ground truth."""
    m = matrix_mod.build_matrix()
    by_name = {f"{p.subsystem}.{p.setting_name}": p for p in m.pointers}

    # XP-announce + economy-log were RETIRED (P0-3 arc PR 2): their scalar
    # SettingSpecs are deleted, so they are no longer pointer settings at
    # all — the binding lane is their sole home now.
    assert "economy.economy_log_channel" not in by_name
    assert "xp.xp_announce_channel" not in by_name

    # Governance role pointers are still deferred (reserved-namespace, no
    # schema home yet — Q-0119); their scalars remain until a home is picked.
    assert by_name["moderation.trusted_role"].disposition == "binding_backed_deferred"
    assert by_name["moderation.trusted_role"].target_binding_declared is False
