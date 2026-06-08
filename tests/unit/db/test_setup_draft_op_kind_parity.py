"""Drift guard: the setup op-kind allowlists must stay in lockstep.

A setup operation must be (1) dispatchable by ``services.setup_operations``,
(2) accepted by the ``utils.db.setup_draft`` Python gate, and (3) permitted by
the ``setup_draft_operations.op_kind`` CHECK constraint.  When PR11 added
``set_role_threshold`` to the dispatcher but not to (2)/(3), the shipped roles
setup section could not actually stage its op (``ValueError`` at the gate).
Migration 059 closed that gap and added ``create_managed_role`` (PR13).

These tests pin all three homes to one set so the class of bug can't recur:
add a new op kind to the dispatcher, the gate, **and** a migration's CHECK in
the same change, or this fails.
"""

from __future__ import annotations

import re
from pathlib import Path

from services import setup_operations
from utils.db import setup_draft as db_setup_draft

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MIGRATION = (
    _REPO_ROOT / "disbot" / "migrations" / "059_setup_draft_op_kinds_role_templates.sql"
)


def _migration_check_kinds() -> set[str]:
    """Extract the op-kind set from migration 059's ``op_kind IN (...)`` CHECK."""
    sql = _MIGRATION.read_text()
    m = re.search(r"op_kind IN \((.*?)\)\s*\)", sql, re.DOTALL)
    assert m, "could not locate the op_kind IN (...) CHECK list in migration 059"
    return set(re.findall(r"'([a-z_]+)'", m.group(1)))


def test_dispatcher_and_db_gate_agree():
    assert setup_operations._KNOWN_KINDS == db_setup_draft._KNOWN_OP_KINDS, (
        "services.setup_operations._KNOWN_KINDS and "
        "utils.db.setup_draft._KNOWN_OP_KINDS drifted — every dispatchable op "
        "kind must be stageable and vice versa.\n"
        f"  dispatcher-only: {setup_operations._KNOWN_KINDS - db_setup_draft._KNOWN_OP_KINDS}\n"
        f"  gate-only:       {db_setup_draft._KNOWN_OP_KINDS - setup_operations._KNOWN_KINDS}"
    )


def test_migration_check_matches_db_gate():
    check = _migration_check_kinds()
    gate = set(db_setup_draft._KNOWN_OP_KINDS)
    assert check == gate, (
        "migration 059's op_kind CHECK and utils.db.setup_draft._KNOWN_OP_KINDS "
        "drifted — widen both together when adding an op kind.\n"
        f"  check-only: {check - gate}\n"
        f"  gate-only:  {gate - check}"
    )


def test_role_template_kinds_present_in_all_three_homes():
    for kind in ("set_role_threshold", "create_managed_role"):
        assert kind in setup_operations._KNOWN_KINDS, f"{kind} missing from dispatcher"
        assert kind in db_setup_draft._KNOWN_OP_KINDS, f"{kind} missing from DB gate"
        assert kind in _migration_check_kinds(), f"{kind} missing from migration CHECK"
