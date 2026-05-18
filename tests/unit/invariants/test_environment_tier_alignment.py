"""Phase 2d PR-2 invariant — environment_tiers.tier matches EnvironmentTier.

Migration 024 ships a CHECK constraint enumerating exactly the values
of :class:`core.runtime.feature_flags.EnvironmentTier`.  Adding a
member to the enum without extending the CHECK constraint would let
the evaluator return a value the DB then rejects on the next write.
Adding to the CHECK without an enum member would let an operator
insert a tier the evaluator silently ignores.
"""

from __future__ import annotations

import re
from pathlib import Path

_MIGRATION = (
    Path(__file__).resolve().parents[3]
    / "disbot"
    / "migrations"
    / "024_environment_tiers.sql"
)


def _extract_tier_literals() -> set[str]:
    sql = _MIGRATION.read_text()
    match = re.search(r"CHECK\s*\(\s*tier\s+IN\s*\(([^)]+)\)\s*\)", sql)
    assert match, "could not locate tier CHECK constraint in migration 024"
    literals = {token.strip().strip("'\"") for token in match.group(1).split(",")}
    return literals


def test_environment_tier_values_match_migration_024_check():
    """Python ``EnvironmentTier`` matches migration 024's CHECK literals."""
    from core.runtime.feature_flags import EnvironmentTier

    db_check = _extract_tier_literals()
    python = {t.value for t in EnvironmentTier}

    missing_in_db = python - db_check
    missing_in_python = db_check - python

    assert not missing_in_db and not missing_in_python, (
        "EnvironmentTier / DB CHECK drift.\n"
        f"  in Python but not DB CHECK: {sorted(missing_in_db)}\n"
        f"  in DB CHECK but not Python: {sorted(missing_in_python)}\n"
        "Fix: extend the CHECK constraint in a new migration AND "
        "update the EnvironmentTier enum.",
    )
