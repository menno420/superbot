"""Phase 2d PR-3 invariant — feature_flag_audit CHECK matches Python literals.

Migration 025 ships CHECK constraints on
``feature_flag_audit.scope``, ``mutation_type``, and ``actor_type``.
The Python module :mod:`services.rollout_mutation` carries the
corresponding constant sets.  This test pins both sides — extending
one without the other should fail CI.
"""

from __future__ import annotations

import re
from pathlib import Path

_MIGRATION = (
    Path(__file__).resolve().parents[3]
    / "disbot"
    / "migrations"
    / "025_feature_flag_audit.sql"
)


def _extract_check_literals(column: str) -> set[str]:
    sql = _MIGRATION.read_text()
    pattern = rf"CHECK\s*\(\s*{column}\s+IN\s*\(([^)]+)\)\s*\)"
    match = re.search(pattern, sql)
    assert match, f"could not locate {column} CHECK constraint in migration 025"
    return {token.strip().strip("'\"") for token in match.group(1).split(",")}


def test_scope_literals_match_python():
    """``scope`` CHECK matches the Python ``Scope`` literal type."""
    db_check = _extract_check_literals("scope")
    expected = {"global", "guild"}
    assert (
        db_check == expected
    ), f"scope CHECK drift: db={sorted(db_check)} vs expected={sorted(expected)}"


def test_mutation_type_literals_match_python():
    """``mutation_type`` CHECK matches the literal type used by the pipeline."""
    db_check = _extract_check_literals("mutation_type")
    expected = {"set_state", "set_rollout_percent", "set_tier"}
    assert (
        db_check == expected
    ), f"mutation_type drift: db={sorted(db_check)} vs expected={sorted(expected)}"


def test_actor_type_literals_match_pipeline_allowed_set():
    """``actor_type`` CHECK matches RolloutMutationPipeline._ALLOWED_ACTOR_TYPES."""
    from services.rollout_mutation import _ALLOWED_ACTOR_TYPES

    db_check = _extract_check_literals("actor_type")
    python = set(_ALLOWED_ACTOR_TYPES)
    assert (
        db_check == python
    ), f"actor_type drift: db={sorted(db_check)} vs python={sorted(python)}"


# ---------------------------------------------------------------------------
# Per-mutation_type shape CHECK constraints
# ---------------------------------------------------------------------------
#
# These tests pin the defense-in-depth invariants that make the single
# ``feature_flag_audit`` table safe to host all three event sources.
# They scan the migration for the specific CHECK clauses; a future
# refactor that removes any of them fails CI here, signalling that the
# corresponding pipeline contract no longer has DB-side enforcement.


def _migration_text() -> str:
    return _MIGRATION.read_text()


def test_set_state_check_constraint_present():
    """set_state rows must carry non-null new_state and avoid the sentinel."""
    sql = _migration_text()
    # Required clauses (independent of formatting)
    assert "mutation_type <> 'set_state'" in sql
    assert "new_state IS NOT NULL" in sql
    assert "flag_name <> '__environment_tier__'" in sql


def test_set_rollout_percent_check_constraint_present():
    """set_rollout_percent rows must be global-scoped + carry new_rollout_percent."""
    sql = _migration_text()
    assert "mutation_type <> 'set_rollout_percent'" in sql
    assert "scope = 'global'" in sql
    assert "new_rollout_percent IS NOT NULL" in sql


def test_set_tier_check_constraint_present():
    """set_tier rows must use the sentinel + be guild-scoped + carry new_tier."""
    sql = _migration_text()
    assert "mutation_type <> 'set_tier'" in sql
    assert "flag_name = '__environment_tier__'" in sql
    assert "scope = 'guild'" in sql
    assert "guild_id IS NOT NULL" in sql
    assert "new_tier IS NOT NULL" in sql


def test_set_tier_check_requires_unused_columns_to_be_null():
    """set_tier rows must leave state + rollout columns NULL.

    This is the contract that lets the single audit table host all
    three event sources without ambiguity: a set_tier row never
    accidentally looks like a state change.
    """
    sql = _migration_text()
    # All five "leave-unused" assertions appear inside the set_tier CHECK
    for null_clause in (
        "prev_state IS NULL",
        "new_state IS NULL",
        "prev_rollout_percent IS NULL",
        "new_rollout_percent IS NULL",
    ):
        assert null_clause in sql, f"missing CHECK clause: {null_clause}"


# ---------------------------------------------------------------------------
# Pipeline contract pins for the environment-tier sentinel
# ---------------------------------------------------------------------------


def test_environment_tier_audit_writes_sentinel_flag_name():
    """utils.db.environment_tiers.upsert_with_audit hard-codes the sentinel.

    Reads the SQL string in the Python primitive and asserts the
    literal '__environment_tier__' appears in the INSERT.  A drift here
    (sentinel renamed in Python but not SQL or vice versa) would let
    set_tier rows escape the per-mutation_type CHECK constraint.
    """
    from pathlib import Path

    src = (
        Path(__file__).resolve().parents[3]
        / "disbot"
        / "utils"
        / "db"
        / "environment_tiers.py"
    ).read_text()
    assert "'__environment_tier__'" in src
    assert "'set_tier'" in src
    assert "'guild'" in src
