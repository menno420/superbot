"""Phase 9g / Track 6 PR 15 — automation_registry tests.

Pins:

* Every documented trigger / action kind appears exactly once in
  the registry tuples.
* Lookup helpers (``get_trigger`` / ``get_action``) return the
  matching spec or ``None``.
* Validation surfaces missing required keys.
* The known-kinds frozensets match the SQL CHECK constraints in
  migrations 032 — pinned by reading the SQL file directly.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from services.automation_registry import (
    ACTIONS,
    KNOWN_ACTION_KINDS,
    KNOWN_TRIGGER_KINDS,
    TRIGGERS,
    ActionSpec,
    TriggerSpec,
    get_action,
    get_trigger,
    validate_action_config,
    validate_trigger_config,
)


def test_trigger_kinds_are_unique():
    kinds = [t.kind for t in TRIGGERS]
    assert len(set(kinds)) == len(kinds)


def test_action_kinds_are_unique():
    kinds = [a.kind for a in ACTIONS]
    assert len(set(kinds)) == len(kinds)


def test_known_trigger_kinds_set_matches_registry():
    assert KNOWN_TRIGGER_KINDS == frozenset(t.kind for t in TRIGGERS)


def test_known_action_kinds_set_matches_registry():
    assert KNOWN_ACTION_KINDS == frozenset(a.kind for a in ACTIONS)


def test_get_trigger_returns_spec_for_known_kind():
    spec = get_trigger("scheduled_time")
    assert isinstance(spec, TriggerSpec)
    assert spec.kind == "scheduled_time"


def test_get_trigger_returns_none_for_unknown():
    assert get_trigger("does_not_exist") is None


def test_get_action_returns_spec_for_known_kind():
    spec = get_action("send_message")
    assert isinstance(spec, ActionSpec)
    assert spec.kind == "send_message"


def test_get_action_returns_none_for_unknown():
    assert get_action("eat_a_sandwich") is None


def test_validate_trigger_config_rejects_unknown_kind():
    errors = validate_trigger_config("garbage", {})
    assert errors and "unknown trigger_kind" in errors[0]


def test_validate_trigger_config_reports_missing_required_keys():
    errors = validate_trigger_config("interval", {})  # missing interval_minutes
    assert errors and "interval_minutes" in errors[0]


def test_validate_trigger_config_passes_when_all_required_present():
    errors = validate_trigger_config("interval", {"interval_minutes": 30})
    assert errors == []


def test_validate_action_config_rejects_unknown_kind():
    errors = validate_action_config("garbage", {})
    assert errors and "unknown action_kind" in errors[0]


def test_validate_action_config_reports_missing_required_keys():
    errors = validate_action_config("send_message", {"channel_id": 1})
    # template still missing
    assert errors and "template" in errors[0]


def test_validate_action_config_passes_when_all_required_present():
    errors = validate_action_config(
        "send_message",
        {"channel_id": 1, "template": "hi"},
    )
    assert errors == []


def test_action_kinds_owner_only_subset():
    """``bind_channel`` and ``create_channel`` require owner."""
    owner_only = {a.kind for a in ACTIONS if a.requires_owner}
    assert owner_only == {"bind_channel", "create_channel"}


# ---------------------------------------------------------------------------
# Alignment with migration 032 CHECK constraints
# ---------------------------------------------------------------------------


def _read_migration() -> str:
    path = (
        Path(__file__).resolve().parents[3]
        / "disbot"
        / "migrations"
        / "032_automation_rules.sql"
    )
    return path.read_text(encoding="utf-8")


def test_known_trigger_kinds_match_migration_check():
    sql = _read_migration()
    match = re.search(
        r"trigger_kind\s+TEXT\s+NOT\s+NULL\s+CHECK\s*\(\s*trigger_kind\s+IN\s*\((.*?)\)\s*\)",
        sql,
        re.DOTALL,
    )
    assert match is not None, "could not find trigger_kind CHECK in migration"
    raw = match.group(1)
    in_sql = frozenset(
        token.strip().strip("'\"")
        for token in raw.split(",")
        if token.strip()
    )
    assert in_sql == KNOWN_TRIGGER_KINDS


def test_known_action_kinds_match_migration_check():
    sql = _read_migration()
    match = re.search(
        r"action_kind\s+TEXT\s+NOT\s+NULL\s+CHECK\s*\(\s*action_kind\s+IN\s*\((.*?)\)\s*\)",
        sql,
        re.DOTALL,
    )
    assert match is not None, "could not find action_kind CHECK in migration"
    raw = match.group(1)
    in_sql = frozenset(
        token.strip().strip("'\"")
        for token in raw.split(",")
        if token.strip()
    )
    assert in_sql == KNOWN_ACTION_KINDS
