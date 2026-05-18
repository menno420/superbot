"""Stale-doc guard for docs/phase-2-completion-readiness.md (PR-10).

Uses resilient marker-and-name assertions (case-insensitive substring
matches; no exact markdown formatting pinning) so the doc can be
re-styled without breaking CI.  The blocker-name check ties the doc to
``services.platform_consistency.SETUP_READINESS_BLOCKERS`` so adding a
new blocker requires updating both files.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from services.platform_consistency import SETUP_READINESS_BLOCKERS

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DOC_PATH = _REPO_ROOT / "docs" / "phase-2-completion-readiness.md"


@pytest.fixture(scope="module")
def doc_text() -> str:
    return _DOC_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def doc_lines(doc_text: str) -> list[str]:
    return doc_text.splitlines()


def test_doc_file_exists():
    assert _DOC_PATH.is_file(), f"Missing doc file: {_DOC_PATH}"


def test_pr_86_marked_merged(doc_lines: list[str]):
    """PR #86 must appear with 'merged' on the same line in the done
    table (clarification #5 — substring assertion, no formatting pin)."""
    matches = [
        ln for ln in doc_lines
        if "#86" in ln and "merged" in ln.lower()
    ]
    assert matches, (
        "Expected a line mentioning PR #86 alongside 'merged' "
        "to indicate PR #86 has landed on main."
    )


def test_migration_028_on_main(doc_lines: list[str]):
    """Migration 028 must appear on a line that also mentions 'main'."""
    matches = [
        ln for ln in doc_lines
        if "028_user_participation_audit.sql" in ln and "main" in ln.lower()
    ]
    assert matches, (
        "Expected '028_user_participation_audit.sql' to appear on the "
        "same line as 'main' (indicating it has landed on main)."
    )


def test_pr_10_listed_as_current_next_work(doc_text: str):
    """PR-10 should be referenced as current next work in the doc."""
    lowered = doc_text.lower()
    assert "pr-10" in lowered or "unified consistency" in lowered, (
        "Expected 'PR-10' or 'Unified Consistency' to appear so reviewers "
        "can locate the current next-work item."
    )


def test_every_setup_readiness_blocker_appears_in_doc(doc_text: str):
    """Every entry in SETUP_READINESS_BLOCKERS must appear in the doc in
    humanised form (snake_case → space-separated, case-insensitive)."""
    lowered = doc_text.lower()
    missing: list[str] = []
    for blocker in SETUP_READINESS_BLOCKERS:
        humanised = blocker.replace("_", " ")
        if humanised not in lowered:
            missing.append(f"{blocker!r} (looked for {humanised!r})")
    assert not missing, (
        "Doc/SETUP_READINESS_BLOCKERS sync gap — add these to the "
        "'Setup-readiness blockers' section:\n  " + "\n  ".join(missing)
    )
