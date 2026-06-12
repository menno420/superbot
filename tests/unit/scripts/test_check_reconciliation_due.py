"""Tests for ``scripts/check_reconciliation_due.py`` — the Q-0107 cadence guard."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
_MOD = REPO_ROOT / "scripts" / "check_reconciliation_due.py"

_spec = importlib.util.spec_from_file_location("check_reconciliation_due", _MOD)
assert _spec and _spec.loader
crd = importlib.util.module_from_spec(_spec)
sys.modules["check_reconciliation_due"] = crd
_spec.loader.exec_module(crd)


def test_not_due_same_band() -> None:
    # marker #737 (band 73), latest #739 (band 73) → not due
    due, latest, marker = crd.is_due(latest=739, marker=737)
    assert due is False
    assert (latest, marker) == (739, 737)


def test_due_when_crossing_multiple_of_ten() -> None:
    # marker #737 (band 73), latest #740 (band 74) → due
    due, _, _ = crd.is_due(latest=740, marker=737)
    assert due is True


def test_due_when_crossing_multiple_bands() -> None:
    due, _, _ = crd.is_due(latest=752, marker=737)
    assert due is True


def test_exactly_on_band_boundary_marker() -> None:
    # last pass landed on #740 (band 74); latest #749 still band 74 → not due
    assert crd.is_due(latest=749, marker=740)[0] is False
    # latest #750 → new band → due
    assert crd.is_due(latest=750, marker=740)[0] is True


def test_no_marker_is_not_due(monkeypatch) -> None:
    # No marker found in current-state → never due (can't compute a cadence).
    monkeypatch.setattr(crd, "_last_reconcile_pr", lambda: None)
    monkeypatch.setattr(crd, "_latest_merged_pr", lambda: 740)
    assert crd.is_due()[0] is False


def test_no_latest_is_not_due(monkeypatch) -> None:
    monkeypatch.setattr(crd, "_latest_merged_pr", lambda: None)
    monkeypatch.setattr(crd, "_last_reconcile_pr", lambda: 737)
    assert crd.is_due()[0] is False


def test_strict_exit_when_due(monkeypatch) -> None:
    monkeypatch.setattr(crd, "is_due", lambda: (True, 740, 737))
    assert crd.main(["--strict"]) == 1
    assert crd.main([]) == 0  # advisory default never fails


def test_strict_exit_when_not_due(monkeypatch) -> None:
    monkeypatch.setattr(crd, "is_due", lambda: (False, 739, 737))
    assert crd.main(["--strict"]) == 0


def test_no_marker_main_exits_zero(monkeypatch) -> None:
    monkeypatch.setattr(crd, "is_due", lambda: (False, 740, None))
    assert crd.main(["--strict"]) == 0
