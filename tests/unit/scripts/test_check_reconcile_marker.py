"""Tests for ``scripts/check_reconcile_marker.py`` — the reconcile-marker consistency guard."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
_MOD = REPO_ROOT / "scripts" / "check_reconcile_marker.py"

_spec = importlib.util.spec_from_file_location("check_reconcile_marker", _MOD)
assert _spec and _spec.loader
crm = importlib.util.module_from_spec(_spec)
sys.modules["check_reconcile_marker"] = crm
_spec.loader.exec_module(crm)


def _marker(n: int, *, band: int, reset: int, doc: str) -> str:
    return (
        f"> **Last reconciliation pass:** PR #{n} (2026-06-26, twenty-sixth Q-0107 cadence pass, "
        f"band-#{band} — [the pass record]({doc}); marker reset to the latest merged PR **#{reset}**). "
        "The next pass is due once merged PRs cross #1500.\n"
    )


def _write_doc(tmp_path: Path, rel: str) -> Path:
    """Create the linked pass-record file under a docs/ root and return that root."""
    docs_root = tmp_path / "docs"
    target = docs_root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("pass record\n", encoding="utf-8")
    return docs_root


# ---------------------------------------------------------------- happy path


def test_consistent_marker_has_no_problems(tmp_path: Path) -> None:
    rel = "planning/reconciliation-pass-2026-06-26-band1470.md"
    docs_root = _write_doc(tmp_path, rel)
    text = _marker(1470, band=1470, reset=1470, doc=rel)
    assert crm.check_marker(text, docs_root=docs_root) == []


def test_marker_not_on_cadence_boundary_still_consistent(tmp_path: Path) -> None:
    # A marker whose number is not itself a multiple of STEP: band = floor(N/STEP)*STEP.
    rel = "planning/reconciliation-pass-2026-06-26-band1470.md"
    docs_root = _write_doc(tmp_path, rel)
    text = _marker(1493, band=1470, reset=1493, doc=rel)  # 1493 // 30 * 30 == 1470
    assert crm.check_marker(text, docs_root=docs_root) == []


# ---------------------------------------------------------------- 1. conflation guard


def test_conflation_leading_pr_differs_from_reset_target(tmp_path: Path) -> None:
    # The real band-#1470 drift: leading #1472 (the pass's own PR) vs reset target #1470.
    rel = "planning/reconciliation-pass-2026-06-26-band1470.md"
    docs_root = _write_doc(tmp_path, rel)
    text = _marker(1472, band=1470, reset=1470, doc=rel)
    problems = crm.check_marker(text, docs_root=docs_root)
    assert len(problems) == 1
    assert "1472" in problems[0] and "1470" in problems[0]


def test_conflation_skipped_when_no_reset_clause(tmp_path: Path) -> None:
    # An older/abbreviated marker without the "reset to ..." clause must not false-red,
    # even when the leading PR is the pass's own number (#1472) — there's nothing to compare against.
    rel = "planning/reconciliation-pass-2026-06-26-band1470.md"
    docs_root = _write_doc(tmp_path, rel)
    text = f"> **Last reconciliation pass:** PR #1472 (band-#1470 — [rec]({rel})). next at #1500.\n"
    assert crm.check_marker(text, docs_root=docs_root) == []


# ---------------------------------------------------------------- 2. band-boundary


def test_band_label_mismatch_flagged(tmp_path: Path) -> None:
    rel = "planning/reconciliation-pass-2026-06-26-band1470.md"
    docs_root = _write_doc(tmp_path, rel)
    text = _marker(
        1470, band=1440, reset=1470, doc=rel
    )  # 1470 // 30 * 30 == 1470, not 1440
    problems = crm.check_marker(text, docs_root=docs_root)
    assert len(problems) == 1
    assert "band-#1440" in problems[0] and "band-#1470" in problems[0]


def test_band_skipped_when_no_band_label(tmp_path: Path) -> None:
    rel = "planning/reconciliation-pass-2026-06-26-band1470.md"
    docs_root = _write_doc(tmp_path, rel)
    text = (
        f"> **Last reconciliation pass:** PR #1470 ([rec]({rel}) — marker reset to the latest "
        "merged PR **#1470**).\n"
    )
    assert crm.check_marker(text, docs_root=docs_root) == []


# ---------------------------------------------------------------- 3. pass-record link


def test_missing_pass_record_doc_flagged(tmp_path: Path) -> None:
    rel = "planning/reconciliation-pass-2026-06-26-band1470.md"
    docs_root = tmp_path / "docs"  # do NOT create the file
    docs_root.mkdir(parents=True, exist_ok=True)
    text = _marker(1470, band=1470, reset=1470, doc=rel)
    problems = crm.check_marker(text, docs_root=docs_root)
    assert len(problems) == 1
    assert rel in problems[0]


def test_doc_link_skipped_when_absent(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    docs_root.mkdir(parents=True, exist_ok=True)
    text = (
        "> **Last reconciliation pass:** PR #1470 (band-#1470; marker reset to the latest "
        "merged PR **#1470**).\n"
    )
    assert crm.check_marker(text, docs_root=docs_root) == []


# ---------------------------------------------------------------- multiple + no-marker


def test_multiple_problems_reported_together(tmp_path: Path) -> None:
    rel = "planning/reconciliation-pass-2026-06-26-band1470.md"
    docs_root = tmp_path / "docs"  # missing doc
    docs_root.mkdir(parents=True, exist_ok=True)
    text = _marker(
        1472, band=1440, reset=1470, doc=rel
    )  # conflation + band + missing doc
    problems = crm.check_marker(text, docs_root=docs_root)
    assert len(problems) == 3


def test_no_marker_is_silent(tmp_path: Path) -> None:
    assert crm.check_marker("no marker here at all\n", docs_root=tmp_path) == []


# ---------------------------------------------------------------- multi-line block (real format)


def test_multiline_blockquote_conflation_is_caught(tmp_path: Path) -> None:
    """The real marker wraps across blockquote lines — the clauses on later lines must be in scope.

    Regression for the bug where a single-physical-line extractor silently skipped the conflation
    check because the "reset to ..." clause sat on a different line than the leading ``PR #N``.
    """
    rel = "planning/reconciliation-pass-2026-06-26-band1470.md"
    docs_root = _write_doc(tmp_path, rel)
    text = (
        "> some preamble\n"
        ">\n"
        "> **Last reconciliation pass:** PR #1472 (2026-06-26, twenty-sixth Q-0107 cadence pass, band-#1470 —\n"
        f"> [the pass record + next-band queue]({rel}); marker reset\n"
        "> to the latest merged PR **#1470**). The next pass is due once merged PRs cross #1500.\n"
        "\n"
        "- some later ledger entry\n"
    )
    problems = crm.check_marker(text, docs_root=docs_root)
    assert (
        len(problems) == 1
    )  # only the conflation; band + doc are consistent across the lines
    assert "1472" in problems[0] and "1470" in problems[0]


def test_multiline_blockquote_consistent_is_clean(tmp_path: Path) -> None:
    rel = "planning/reconciliation-pass-2026-06-26-band1470.md"
    docs_root = _write_doc(tmp_path, rel)
    text = (
        "> **Last reconciliation pass:** PR #1470 (2026-06-26, twenty-sixth Q-0107 cadence pass, band-#1470 —\n"
        f"> [the pass record + next-band queue]({rel}); marker reset\n"
        "> to the latest merged PR **#1470**). The next pass is due once merged PRs cross #1500.\n"
        "\n"
        "- some later ledger entry that mentions #9999 and band-#1500 should not leak in\n"
    )
    assert crm.check_marker(text, docs_root=docs_root) == []


# ---------------------------------------------------------------- live current-state.md


def test_live_current_state_marker_is_consistent() -> None:
    """The committed marker in docs/current-state.md must be consistent (drift fixed this PR)."""
    assert crm.check_marker() == []


# ---------------------------------------------------------------- STEP stays in sync


def test_step_matches_reconciliation_due() -> None:
    """STEP mirrors check_reconciliation_due.STEP — they must not drift apart."""
    rd_path = REPO_ROOT / "scripts" / "check_reconciliation_due.py"
    rd_spec = importlib.util.spec_from_file_location(
        "check_reconciliation_due", rd_path
    )
    assert rd_spec and rd_spec.loader
    rd = importlib.util.module_from_spec(rd_spec)
    sys.modules["check_reconciliation_due"] = rd
    rd_spec.loader.exec_module(rd)
    assert crm.STEP == rd.STEP
