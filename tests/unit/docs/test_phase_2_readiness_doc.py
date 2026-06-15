"""Stale-doc guard for docs/archive/phase-2-completion-readiness.md (PR-10).

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
_DOC_PATH = _REPO_ROOT / "docs" / "archive" / "phase-2-completion-readiness.md"


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
    matches = [ln for ln in doc_lines if "#86" in ln and "merged" in ln.lower()]
    assert matches, (
        "Expected a line mentioning PR #86 alongside 'merged' "
        "to indicate PR #86 has landed on main."
    )


def test_migration_028_on_main(doc_lines: list[str]):
    """Migration 028 must appear on a line that also mentions 'main'."""
    matches = [
        ln
        for ln in doc_lines
        if "028_user_participation_audit.sql" in ln and "main" in ln.lower()
    ]
    assert matches, (
        "Expected '028_user_participation_audit.sql' to appear on the "
        "same line as 'main' (indicating it has landed on main)."
    )


def test_doc_marks_phase_2_queue_historical(doc_text: str):
    """The old PR-10 queue must not present itself as current next work."""
    lowered = doc_text.lower()
    assert "historical phase-2 snapshot" in lowered
    assert "superseded as" in lowered and "live next-work queue" in lowered


def test_every_setup_readiness_blocker_appears_in_doc(doc_text: str):
    """Every entry in SETUP_READINESS_BLOCKERS must appear in the doc in
    humanised form (snake_case → space-separated, case-insensitive).

    PR-03: ``SETUP_READINESS_BLOCKERS`` is now derived from
    ``services.setup_blockers.blocker_ids()`` but the bare-string
    contract is preserved, so this assertion still works unchanged.
    """
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


# ---------------------------------------------------------------------------
# PR-03: resolved-marker cross-check
# ---------------------------------------------------------------------------


def test_blocker_ids_match_blocker_specs():
    """The derived ID list must match the underlying ``BlockerSpec`` IDs.

    Prevents drift between ``services.setup_blockers.BLOCKERS`` and
    ``platform_consistency.SETUP_READINESS_BLOCKERS`` (which is now a
    re-export of ``blocker_ids()``)."""
    from services import setup_blockers

    spec_ids = tuple(b.id for b in setup_blockers.BLOCKERS)
    assert SETUP_READINESS_BLOCKERS == spec_ids


def test_every_blocker_has_resolution_provider_and_doc_anchor():
    """Each spec must declare a doc_anchor + a callable status_provider.

    Doc anchor is the "where do I read more?" link operators follow
    when a blocker is pending; status_provider is the sync resolution
    check the readiness collector consumes."""
    from services import setup_blockers

    missing_anchor: list[str] = []
    missing_provider: list[str] = []
    for spec in setup_blockers.BLOCKERS:
        if not spec.doc_anchor:
            missing_anchor.append(spec.id)
        if not callable(spec.status_provider):
            missing_provider.append(spec.id)
    assert not missing_anchor, "BlockerSpec(s) missing doc_anchor:\n  " + "\n  ".join(
        missing_anchor
    )
    assert (
        not missing_provider
    ), "BlockerSpec(s) missing status_provider:\n  " + "\n  ".join(missing_provider)


def test_blocker_status_provider_returns_valid_literal():
    """Every status_provider must return a member of BlockerStatus.

    Fail-safe ``status_for`` wrapper catches exceptions and returns
    ``"unknown"``, but this test exercises the providers directly to
    catch silent shape drift."""
    from services import setup_blockers

    valid = {"resolved", "in_progress", "pending", "blocked", "unknown"}
    invalid: list[str] = []
    for spec in setup_blockers.BLOCKERS:
        status = setup_blockers.status_for(spec)
        if status not in valid:
            invalid.append(f"{spec.id}: returned {status!r}")
    assert (
        not invalid
    ), "BlockerSpec.status_provider returned unknown literal:\n  " + "\n  ".join(
        invalid
    )
