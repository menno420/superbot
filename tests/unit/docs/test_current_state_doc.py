"""Structure guard for docs/current-state.md (doc-restructure session).

``current-state.md`` is the living "what is true right now?" router — read
second, right after ``.claude/CLAUDE.md``.  This guard pins its *structure*
(the canonical section headers, the freshness stamp, and the two trust
rules) without pinning volatile content (PR numbers, dates), so the file
can be updated every session without breaking CI yet cannot silently rot
into a non-router.

Resilient case-insensitive substring assertions, mirroring
``test_phase_2_readiness_doc.py``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DOC_PATH = _REPO_ROOT / "docs" / "current-state.md"

# Canonical router sections (substring, case-insensitive). Renaming one is a
# deliberate act that should update this list in the same commit.
_REQUIRED_SECTIONS = (
    "stability baseline",
    "in flight",
    "recently shipped",
    "next candidates",
    "gates",
    "known ux follow-ups",
    "off-limits",
    "where to read next",
)


@pytest.fixture(scope="module")
def doc_text() -> str:
    return _DOC_PATH.read_text(encoding="utf-8")


def test_doc_file_exists() -> None:
    assert _DOC_PATH.is_file(), f"Missing doc file: {_DOC_PATH}"


def test_has_last_updated_stamp(doc_text: str) -> None:
    """Freshness depends on a visible date stamp; without it the snapshot
    can be neither trusted nor distrusted."""
    assert "last updated:" in doc_text.lower(), (
        "current-state.md must carry a 'Last updated:' stamp so readers can "
        "judge freshness."
    )


def test_has_required_sections(doc_text: str) -> None:
    lowered = doc_text.lower()
    missing = [s for s in _REQUIRED_SECTIONS if s not in lowered]
    assert (
        not missing
    ), "current-state.md is missing canonical router sections:\n  " + "\n  ".join(
        missing
    )


def test_states_source_and_pr_precedence(doc_text: str) -> None:
    """The router must never become a false authority: source + merged PRs
    win, and in-flight state is verified against live GitHub."""
    lowered = doc_text.lower()
    assert (
        "win" in lowered and "source" in lowered and "merged pr" in lowered
    ), "current-state.md must state that source code and merged PRs win over it."
    assert "github" in lowered, (
        "current-state.md must tell readers to verify in-flight PRs against live "
        "GitHub (the snapshot goes stale on every push)."
    )
