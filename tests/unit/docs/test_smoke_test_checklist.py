"""Stale-doc guard for docs/smoke-test-checklist.md (PR-05).

Pins the 1:1 correspondence between the checklist's bullets and the
fields on ``services.platform_consistency.ReadinessSnapshot``.
Adding a snapshot field without surfacing it here (or removing one
without removing the matching bullet) fails CI.

The assertion model mirrors
``tests/unit/docs/test_phase_2_readiness_doc.py``: case-insensitive
substring matches against humanised field names, so the doc can be
re-styled freely.  The fields tested below are the human-relevant
buckets in ``ReadinessSnapshot``; bookkeeping fields like
``generated_at`` are deliberately omitted because they are not
operator-actionable.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from services.platform_consistency import ReadinessSnapshot

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DOC_PATH = _REPO_ROOT / "docs" / "smoke-test-checklist.md"

# Fields on ReadinessSnapshot that operators reason about directly.
# Adding a new actionable field to the snapshot requires adding both
# the field name here AND a matching bullet in the doc.
_ACTIONABLE_SNAPSHOT_FIELDS: tuple[str, ...] = (
    "consistency_overall_status",
    "consistency_report_at",
    "consistency_blocking_sections",
    "startup_outcomes",
    "ledger_built",
    "settings_registry_built",
    "customization_catalogue_built",
    "provisioning_catalogue_built",
    "tasks_active_count",
    "tasks_active_names",
)

# Pure-bookkeeping fields the operator never reads directly.  Listed
# here so the "every field is covered" test below has a clean
# allowlist — adding a new bookkeeping field requires explicit opt-in.
_BOOKKEEPING_SNAPSHOT_FIELDS: tuple[str, ...] = ("generated_at",)


@pytest.fixture(scope="module")
def doc_text() -> str:
    return _DOC_PATH.read_text(encoding="utf-8").lower()


def test_doc_file_exists():
    assert _DOC_PATH.is_file(), f"Missing smoke checklist doc: {_DOC_PATH}"


def test_every_actionable_snapshot_field_appears_in_doc(doc_text: str):
    """Every actionable ``ReadinessSnapshot`` field must appear in the
    checklist (case-insensitive substring; doc style is free)."""
    missing: list[str] = []
    for field in _ACTIONABLE_SNAPSHOT_FIELDS:
        if field not in doc_text:
            missing.append(field)
    assert not missing, (
        "Smoke checklist missing bullets for these ReadinessSnapshot "
        "fields:\n  " + "\n  ".join(missing)
    )


def test_actionable_fields_exhaust_snapshot_shape():
    """The union of actionable + bookkeeping field lists must equal
    the actual ``ReadinessSnapshot`` dataclass shape.  A new field on
    the snapshot must be classified explicitly so the doc stays in
    sync."""
    actual = {f.name for f in dataclasses.fields(ReadinessSnapshot)}
    declared = set(_ACTIONABLE_SNAPSHOT_FIELDS) | set(_BOOKKEEPING_SNAPSHOT_FIELDS)
    only_in_dataclass = actual - declared
    only_in_test = declared - actual
    assert not only_in_dataclass, (
        "ReadinessSnapshot gained field(s) without doc-test "
        "classification — add to _ACTIONABLE_SNAPSHOT_FIELDS or "
        "_BOOKKEEPING_SNAPSHOT_FIELDS:\n  " + "\n  ".join(sorted(only_in_dataclass))
    )
    assert not only_in_test, (
        "Doc-test references field(s) no longer on ReadinessSnapshot "
        "— remove from _ACTIONABLE_SNAPSHOT_FIELDS / "
        "_BOOKKEEPING_SNAPSHOT_FIELDS:\n  " + "\n  ".join(sorted(only_in_test))
    )


def test_doc_mentions_canonical_startup_phases(doc_text: str):
    """Every known startup phase from
    ``core.runtime.startup_outcome.KNOWN_PHASES`` must appear in the
    doc so operators can tick the matching outcome bullet."""
    from core.runtime.startup_outcome import KNOWN_PHASES

    missing = [p for p in KNOWN_PHASES if p not in doc_text]
    assert not missing, (
        "Smoke checklist missing startup phase bullets:\n  "
        + "\n  ".join(missing)
    )


def test_doc_mentions_every_setup_slash_command(doc_text: str):
    """Every live setup slash command must appear in the wizard smoke
    block.  The five commands are pinned by source — adding a sixth
    requires updating both ``cogs/setup_cog.py`` and this checklist
    so operators have a verification step for the new surface."""
    for cmd in (
        "/setup-status",
        "/setup-reset",
        "/setup-skip",
        "/setup-unskip",
        "/setup-depth",
    ):
        assert cmd.lower() in doc_text, (
            f"Smoke checklist must mention {cmd} so operators can "
            "tick the wizard smoke bullet for it."
        )


def test_doc_mentions_setup_preflight_diff(doc_text: str):
    """PR-04a/04b: the setup preflight diff is a smoke-relevant
    surface.  Operators verify both:
    * preflight shows when SETUP_PREFLIGHT_DIFF is on (the default).
    * the normalized comparison does not flag type-equivalent values
      (bool True vs string "true") as a diff.
    """
    lowered = doc_text  # already lowered by the fixture
    assert "preflight" in lowered, (
        "Smoke checklist must mention the setup preflight diff."
    )
    assert "values_equivalent" in lowered or "type-equivalent" in lowered, (
        "Smoke checklist must call out the normalized comparison so "
        "operators check for type-mismatch false positives."
    )


def test_doc_mentions_setup_blocker_output(doc_text: str):
    """PR-03: setup blockers come from the dynamic
    ``services.setup_blockers.BLOCKERS`` registry.  The checklist
    must remind operators to verify the live state matches the
    registry rather than the stale static list."""
    assert "setup_blockers" in doc_text or "setup blocker output" in doc_text, (
        "Smoke checklist must mention the setup blocker output and "
        "its source-of-truth (services.setup_blockers.BLOCKERS)."
    )


def test_doc_mentions_setup_readiness_command(doc_text: str):
    """``!platform setup-readiness`` is the operator-facing surface
    for the per-guild readiness inventory.  Smoke must include it."""
    assert "setup-readiness" in doc_text, (
        "Smoke checklist must mention !platform setup-readiness."
    )


def test_doc_pins_shutdown_drain_budget(doc_text: str):
    """PR-02b preserved the 5 s shutdown drain budget.  The checklist
    must mention it so a regression is caught at smoke time."""
    assert "5 s" in doc_text or "5s" in doc_text or "5 seconds" in doc_text, (
        "Smoke checklist must reference the 5 s shutdown drain budget."
    )
