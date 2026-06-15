"""Static SQL-shape pins for migration 058 (server-management PR8).

Mirrors ``test_migration_051_main_server_backfill.py`` /
``test_migration_057_operational_health_findings.py``: we cannot run Postgres in
unit CI (``tests/conftest.py`` has no DB fixture, ``code-quality.yml`` runs no
Postgres service), but we CAN pin the *shape* of the schema change so a drive-by
edit that turns the additive, behaviour-neutral column into something that
touches the RC-5 CHECK, the primary key, or existing data fails here instead of
silently in production.

The live behaviour (column applies, existing rows backfill to 1, the reader
returns it) is exercised against a real database in
``test_cleanup_policies_integration.py`` (skipped when no Postgres is reachable).
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MIGRATION = _REPO_ROOT / "disbot" / "migrations" / "058_cleanup_policy_version.sql"


def _collapse(text: str) -> str:
    """Collapse whitespace runs to a single space (line-wrap-insensitive)."""
    return re.sub(r"\s+", " ", text).strip()


def _migration_sql() -> str:
    """Migration text with ``-- …`` line comments stripped, then collapsed."""
    no_comments = "\n".join(
        line.split("--", 1)[0] for line in _MIGRATION.read_text().splitlines()
    )
    return _collapse(no_comments)


def test_migration_file_exists():
    assert _MIGRATION.is_file(), f"{_MIGRATION} missing"


def test_adds_policy_version_column_to_cleanup_policies():
    """The migration adds exactly the ``policy_version`` column."""
    sql = _migration_sql()
    assert "ALTER TABLE cleanup_policies" in sql
    assert "ADD COLUMN IF NOT EXISTS policy_version" in sql


def test_policy_version_is_not_null_default_one():
    """Existing rows must backfill to version 1 via the column DEFAULT, and the
    column is NOT NULL so every row is self-describing."""
    assert "policy_version INTEGER NOT NULL DEFAULT 1" in _migration_sql()


def test_add_column_is_idempotent():
    """``IF NOT EXISTS`` keeps the forward-only migration re-runnable; a bare
    ``ADD COLUMN`` would abort the second apply and take boot down."""
    sql = _migration_sql()
    assert re.search(r"ADD COLUMN(?! IF NOT EXISTS)", sql) is None, (
        "the policy_version ADD COLUMN must use IF NOT EXISTS"
    )


def test_migration_is_additive_only_preserving_rc5_and_pk():
    """RC-5 + behaviour-identical guard: 058 must ONLY add a column — it must not
    drop/redefine the scope_type CHECK or the primary key, nor mutate existing
    rows. Any of those would change cleanup resolution or thread inheritance."""
    sql = _migration_sql()
    assert "DROP" not in sql, "058 must not DROP anything"
    assert "CHECK" not in sql, "058 must not touch the scope_type CHECK (RC-5)"
    assert "PRIMARY KEY" not in sql, "058 must not touch the primary key"
    assert "UPDATE " not in sql, "058 must not UPDATE existing rows (DEFAULT backfills)"
    assert "DELETE " not in sql, "058 must not DELETE rows"
