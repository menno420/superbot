"""Phase 2 PR-5 — pure ``classify_candidate`` matrix.

The classifier is intentionally synchronous so the full classification
matrix can be exercised without DB or Discord mocking.  Each test
covers one ``Classification`` value.
"""

from __future__ import annotations

import pytest

from core.resources.status import ResourceStatus
from core.runtime.subsystem_schema import BindingKind
from services.binding_backfill import (
    Classification,
    MigratedKey,
    classify_candidate,
)

_KEY = MigratedKey(
    legacy_key="xp_announce_channel",
    subsystem="xp",
    binding_name="announce_channel",
    kind=BindingKind.CHANNEL,
)


# ---------------------------------------------------------------------------
# Schema gate
# ---------------------------------------------------------------------------


def test_blocked_no_schema_short_circuits():
    """Even when both sides have values, schema-undeclared bindings block."""
    classification, reason = classify_candidate(
        migrated_key=_KEY,
        legacy_raw="123",
        legacy_validated_status=ResourceStatus.BOUND,
        binding_target_id=123,
        binding_status=ResourceStatus.BOUND,
        schema_declared=False,
    )
    assert classification is Classification.BLOCKED_NO_SCHEMA
    assert "no registered SubsystemSchema" in reason


# ---------------------------------------------------------------------------
# Both absent
# ---------------------------------------------------------------------------


def test_both_absent():
    classification, _ = classify_candidate(
        migrated_key=_KEY,
        legacy_raw=None,
        legacy_validated_status=None,
        binding_target_id=None,
        binding_status=None,
        schema_declared=True,
    )
    assert classification is Classification.BOTH_ABSENT


def test_empty_legacy_treated_as_absent():
    """Empty-string legacy is the legacy KV "missing" sentinel."""
    classification, _ = classify_candidate(
        migrated_key=_KEY,
        legacy_raw="",
        legacy_validated_status=None,
        binding_target_id=None,
        binding_status=None,
        schema_declared=True,
    )
    assert classification is Classification.BOTH_ABSENT


# ---------------------------------------------------------------------------
# Binding only
# ---------------------------------------------------------------------------


def test_binding_only_bound():
    classification, _ = classify_candidate(
        migrated_key=_KEY,
        legacy_raw=None,
        legacy_validated_status=None,
        binding_target_id=999,
        binding_status=ResourceStatus.BOUND,
        schema_declared=True,
    )
    assert classification is Classification.BINDING_ONLY


def test_binding_only_status_not_bound():
    """Binding row exists with status MISSING and no legacy."""
    classification, _ = classify_candidate(
        migrated_key=_KEY,
        legacy_raw=None,
        legacy_validated_status=None,
        binding_target_id=None,
        binding_status=ResourceStatus.MISSING,
        schema_declared=True,
    )
    assert classification is Classification.BINDING_STATUS_NOT_BOUND


# ---------------------------------------------------------------------------
# Legacy only — every sub-case
# ---------------------------------------------------------------------------


def test_legacy_only_candidate_valid():
    classification, reason = classify_candidate(
        migrated_key=_KEY,
        legacy_raw="123",
        legacy_validated_status=ResourceStatus.BOUND,
        binding_target_id=None,
        binding_status=None,
        schema_declared=True,
    )
    assert classification is Classification.CANDIDATE_VALID
    assert "validates" in reason


def test_legacy_only_target_missing():
    classification, _ = classify_candidate(
        migrated_key=_KEY,
        legacy_raw="123",
        legacy_validated_status=ResourceStatus.MISSING,
        binding_target_id=None,
        binding_status=None,
        schema_declared=True,
    )
    assert classification is Classification.CANDIDATE_INVALID_TARGET_MISSING


def test_legacy_only_wrong_kind():
    """Legacy value points at a Discord object whose kind doesn't match."""
    classification, _ = classify_candidate(
        migrated_key=_KEY,
        legacy_raw="123",
        legacy_validated_status=ResourceStatus.INVALID,
        binding_target_id=None,
        binding_status=None,
        schema_declared=True,
    )
    assert classification is Classification.CANDIDATE_INVALID_WRONG_KIND


def test_legacy_only_unparseable():
    classification, _ = classify_candidate(
        migrated_key=_KEY,
        legacy_raw="not-a-number",
        legacy_validated_status=None,
        binding_target_id=None,
        binding_status=None,
        schema_declared=True,
    )
    assert classification is Classification.CANDIDATE_INVALID_UNPARSEABLE


def test_legacy_only_unresolved_treated_as_missing():
    classification, _ = classify_candidate(
        migrated_key=_KEY,
        legacy_raw="123",
        legacy_validated_status=ResourceStatus.UNRESOLVED,
        binding_target_id=None,
        binding_status=None,
        schema_declared=True,
    )
    assert classification is Classification.CANDIDATE_INVALID_TARGET_MISSING


# ---------------------------------------------------------------------------
# Both present — match / disagree / status-not-bound
# ---------------------------------------------------------------------------


def test_both_present_match():
    classification, _ = classify_candidate(
        migrated_key=_KEY,
        legacy_raw="123",
        legacy_validated_status=ResourceStatus.BOUND,
        binding_target_id=123,
        binding_status=ResourceStatus.BOUND,
        schema_declared=True,
    )
    assert classification is Classification.MATCH


def test_both_present_disagree():
    classification, reason = classify_candidate(
        migrated_key=_KEY,
        legacy_raw="123",
        legacy_validated_status=ResourceStatus.BOUND,
        binding_target_id=456,
        binding_status=ResourceStatus.BOUND,
        schema_declared=True,
    )
    assert classification is Classification.DISAGREE
    assert "operator must reconcile" in reason


def test_both_present_binding_not_bound_wins_over_match():
    """When the binding status is not BOUND, surface that instead of matching."""
    classification, _ = classify_candidate(
        migrated_key=_KEY,
        legacy_raw="123",
        legacy_validated_status=ResourceStatus.BOUND,
        binding_target_id=123,
        binding_status=ResourceStatus.MISSING,
        schema_declared=True,
    )
    assert classification is Classification.BINDING_STATUS_NOT_BOUND


def test_both_present_legacy_unparseable_keeps_binding():
    """Junk legacy + valid binding row → trust the binding."""
    classification, _ = classify_candidate(
        migrated_key=_KEY,
        legacy_raw="garbage",
        legacy_validated_status=None,
        binding_target_id=123,
        binding_status=ResourceStatus.BOUND,
        schema_declared=True,
    )
    assert classification is Classification.BINDING_ONLY


# ---------------------------------------------------------------------------
# WRITABLE_CLASSIFICATIONS — only the safe candidate survives
# ---------------------------------------------------------------------------


def test_only_candidate_valid_is_writable():
    """The PR-6 write phase consumes ONLY ``CANDIDATE_VALID`` candidates."""
    from services.binding_backfill import WRITABLE_CLASSIFICATIONS

    assert WRITABLE_CLASSIFICATIONS == frozenset({Classification.CANDIDATE_VALID})
