"""Phase 2c PR-8 invariant — participation state literals align.

Migration 027 ships CHECK constraints on
``user_participation.state`` and
``user_visibility_overrides.visibility``.  The Python module
:mod:`utils.db.user_participation` carries matching ``frozenset``s;
this test pins both sides.
"""

from __future__ import annotations

import re
from pathlib import Path

_MIGRATION = (
    Path(__file__).resolve().parents[3]
    / "disbot"
    / "migrations"
    / "027_user_participation.sql"
)


def _extract_check(column: str) -> set[str]:
    sql = _MIGRATION.read_text()
    matches = re.findall(
        rf"CHECK\s*\(\s*{column}\s+IN\s*\(([^)]+)\)\s*\)",
        sql,
    )
    assert matches, f"could not locate {column} CHECK in migration 027"
    out: set[str] = set()
    for clause in matches:
        for token in clause.split(","):
            literal = token.strip().strip("'\"")
            if literal:
                out.add(literal)
    return out


def test_participation_state_literals_match():
    from utils.db.user_participation import PARTICIPATION_STATES

    db_check = _extract_check("state")
    python = set(PARTICIPATION_STATES)
    assert db_check == python, (
        "user_participation state drift.\n"
        f"  in Python but not DB CHECK: {sorted(python - db_check)}\n"
        f"  in DB CHECK but not Python: {sorted(db_check - python)}"
    )


def test_visibility_literals_match():
    from utils.db.user_participation import VISIBILITY_STATES

    db_check = _extract_check("visibility")
    python = set(VISIBILITY_STATES)
    assert db_check == python, (
        "user_visibility_overrides visibility drift.\n"
        f"  in Python but not DB CHECK: {sorted(python - db_check)}\n"
        f"  in DB CHECK but not Python: {sorted(db_check - python)}"
    )


def test_all_tables_carry_guild_id():
    """Every participation table MUST include guild_id (consistency ledger §3)."""
    sql = _MIGRATION.read_text()
    for table in (
        "user_participation",
        "user_subscriptions",
        "user_preferences",
        "user_visibility_overrides",
    ):
        # Match the CREATE TABLE block for this name
        match = re.search(
            rf"CREATE TABLE IF NOT EXISTS {table}\s*\(([^;]+)\)\s*;",
            sql,
            re.DOTALL,
        )
        assert match, f"could not locate CREATE TABLE for {table}"
        body = match.group(1)
        assert (
            "guild_id" in body
        ), f"{table} does not include guild_id — Phase 2c retention contract"


def test_accessor_enums_have_distinct_values():
    """ParticipationState and VisibilityState values do not collide."""
    from utils.user_config_accessors import ParticipationState, VisibilityState

    p_values = {s.value for s in ParticipationState}
    v_values = {s.value for s in VisibilityState}
    overlap = p_values & v_values
    assert (
        not overlap
    ), f"ParticipationState ∩ VisibilityState = {overlap}; values must be distinct"
