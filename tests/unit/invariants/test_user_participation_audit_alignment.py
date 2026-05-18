"""Phase 2c PR-9 invariant — user_participation_audit literals align.

Migration 028 ships CHECK constraints on
``user_participation_audit``:

* ``mutation_type`` — one of the four pipeline entrypoints
* ``actor_type`` — actor model
* ``prev_state`` / ``new_state`` — participation enum
* ``prev_visibility`` / ``new_visibility`` — visibility enum
* Per-``mutation_type`` shape clauses (set_participation /
  set_subscription / set_preference / set_visibility) enforcing
  which key/value columns must be NULL or NOT NULL.

The Python pipeline carries matching ``frozenset``s in
:mod:`services.participation_mutation`.  This test pins both
sides so a drift on either fails CI.
"""

from __future__ import annotations

import re
from pathlib import Path

_MIGRATION = (
    Path(__file__).resolve().parents[3]
    / "disbot"
    / "migrations"
    / "028_user_participation_audit.sql"
)


def _read() -> str:
    return _MIGRATION.read_text()


def _extract_in_set(column: str) -> set[str]:
    sql = _read()
    pattern = rf"CHECK\s*\(\s*{column}\s+IN\s*\(([^)]+)\)\s*\)"
    match = re.search(pattern, sql)
    assert match, f"could not locate {column} CHECK constraint"
    return {
        tok.strip().strip("'\"") for tok in match.group(1).split(",") if tok.strip()
    }


# ---------------------------------------------------------------------------
# Top-level literal CHECK constraints
# ---------------------------------------------------------------------------


def test_mutation_type_literals_match_pipeline():
    """``mutation_type`` CHECK matches the four pipeline entrypoint names."""
    db_check = _extract_in_set("mutation_type")
    expected = {
        "set_participation",
        "set_subscription",
        "set_preference",
        "set_visibility",
    }
    assert (
        db_check == expected
    ), f"mutation_type drift: db={sorted(db_check)} vs expected={sorted(expected)}"


def test_actor_type_literals_match_pipeline_allowed_set():
    from services.participation_mutation import _ALLOWED_ACTOR_TYPES

    db_check = _extract_in_set("actor_type")
    python = set(_ALLOWED_ACTOR_TYPES)
    assert (
        db_check == python
    ), f"actor_type drift: db={sorted(db_check)} vs python={sorted(python)}"


def test_state_literals_match_migration_027():
    """audit ``prev_state`` / ``new_state`` literals match
    user_participation.state from migration 027."""
    from utils.db.user_participation import PARTICIPATION_STATES

    sql = _read()
    # Both prev_state and new_state share the same allow-list
    state_clauses = re.findall(
        r"prev_state IS NULL OR prev_state IN \(([^)]+)\)",
        sql,
    )
    state_clauses += re.findall(
        r"new_state IS NULL OR new_state IN \(([^)]+)\)",
        sql,
    )
    assert (
        len(state_clauses) == 2
    ), "expected one CHECK clause for each of prev_state/new_state"
    literals = {tok.strip().strip("'\"") for tok in state_clauses[0].split(",")}
    assert literals == set(
        PARTICIPATION_STATES
    ), f"state CHECK drift: audit={sorted(literals)} vs python={sorted(PARTICIPATION_STATES)}"


def test_visibility_literals_match_migration_027():
    from utils.db.user_participation import VISIBILITY_STATES

    sql = _read()
    vis_clauses = re.findall(
        r"prev_visibility IS NULL OR prev_visibility IN \(([^)]+)\)",
        sql,
    )
    vis_clauses += re.findall(
        r"new_visibility IS NULL OR new_visibility IN \(([^)]+)\)",
        sql,
    )
    assert len(vis_clauses) == 2
    literals = {tok.strip().strip("'\"") for tok in vis_clauses[0].split(",")}
    assert literals == set(VISIBILITY_STATES)


# ---------------------------------------------------------------------------
# Per-mutation_type shape CHECK clauses
# ---------------------------------------------------------------------------


def test_set_participation_shape_check_present():
    sql = _read()
    assert "mutation_type <> 'set_participation'" in sql
    assert "subsystem IS NOT NULL" in sql
    assert "new_state IS NOT NULL" in sql


def test_set_subscription_shape_check_present():
    sql = _read()
    assert "mutation_type <> 'set_subscription'" in sql
    assert "topic IS NOT NULL" in sql
    assert "new_enabled IS NOT NULL" in sql


def test_set_preference_shape_check_present():
    sql = _read()
    assert "mutation_type <> 'set_preference'" in sql
    assert "key IS NOT NULL" in sql
    assert "new_value IS NOT NULL" in sql


def test_set_visibility_shape_check_present():
    sql = _read()
    assert "mutation_type <> 'set_visibility'" in sql
    assert "new_visibility IS NOT NULL" in sql


def test_unused_columns_required_null_per_mutation_type():
    """Each shape clause forces the unused concern columns to NULL.

    Without these, a malformed row (e.g. set_preference with a
    subsystem set) could escape the per-mutation_type contract.
    """
    sql = _read()
    # Spot-check a few "must be NULL" assertions
    for null_clause in (
        # set_participation excludes topic + key + value/enabled/visibility
        "topic IS NULL",
        "key IS NULL",
        "prev_enabled IS NULL AND new_enabled IS NULL",
        "prev_value IS NULL AND new_value IS NULL",
        "prev_visibility IS NULL AND new_visibility IS NULL",
        # set_subscription excludes key + state + value + visibility
        "prev_state IS NULL AND new_state IS NULL",
    ):
        assert null_clause in sql, f"missing NULL CHECK clause: {null_clause}"
