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
    # STEP=30: marker #737 (band 24: 720–749), latest #739 (band 24) → not due
    due, latest, marker = crd.is_due(latest=739, marker=737)
    assert due is False
    assert (latest, marker) == (739, 737)


def test_due_when_crossing_band() -> None:
    # STEP=30: marker #737 (band 24: 720–749), latest #750 (band 25) → due
    due, _, _ = crd.is_due(latest=750, marker=737)
    assert due is True


def test_due_when_crossing_multiple_bands() -> None:
    # STEP=30: marker #737 (band 24), latest #810 (band 27) → due
    due, _, _ = crd.is_due(latest=810, marker=737)
    assert due is True


def test_exactly_on_band_boundary_marker() -> None:
    # STEP=30: last pass landed on #750 (band boundary); latest #779 still band 25 → not due
    assert crd.is_due(latest=779, marker=750)[0] is False
    # latest #780 → new band (26) → due
    assert crd.is_due(latest=780, marker=750)[0] is True


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


def test_issue_body_tracks_the_live_cadence() -> None:
    """The canonical issue body is built from STEP, so it can never drift from the
    firing cadence (BUG-0016: the workflow's old hardcoded string said "multiple-of-20" /
    "next ~9 PRs" long after the cadence became 30 + full-band)."""
    body = crd.issue_body()
    assert f"A {crd.STEP}-PR band was crossed" in body
    assert f"cadence {crd.STEP} per Q-0134" in body
    assert "next full band" in body
    # The stale strings the bug was about must be gone.
    assert "multiple-of-20" not in body
    assert "~9 PRs" not in body


def test_issue_body_flag_prints_body_and_exits_zero(capsys) -> None:
    assert crd.main(["--issue-body"]) == 0
    out = capsys.readouterr().out
    assert out.strip() == crd.issue_body()


def test_merge_subject_regex_covers_all_three_styles() -> None:
    """The 'Merge PR #' alternative is load-bearing: MCP merges ("Merge PR #N: …")
    are the dominant style since 2026-06, and missing them froze the latest-PR
    detection at #751 while #762 was merged (the 2026-06-12 night pass bug).
    Anchoring is equally load-bearing since 2026-07-10: an un-anchored "PR #N"
    also matched cross-repo references inside ordinary branch-commit subjects
    (the phantom-"#104" false-red)."""
    subjects = (
        ("Merge pull request #730 from menno420/branch", 730),
        ("docs(hermes): live-verified 2026-06-12 (#751)", 751),
        ("Merge PR #762: UX Lab PR C — mock studio", 762),
    )
    for subject, expected in subjects:
        match = crd._MERGE_SUBJECT_RE.search(subject)
        assert match, subject
        assert int(match.group(1) or match.group(2)) == expected, subject
    # Cross-repo reference mid-subject: must NOT match (phantom-#104 class).
    assert (
        crd._MERGE_SUBJECT_RE.search(
            "docs: never-ask ruling (superbot-next ORDER 010, PR #104); pkg updated"
        )
        is None
    )
