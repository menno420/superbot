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
