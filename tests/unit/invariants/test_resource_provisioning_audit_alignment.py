"""S4.5 invariant — resource_provisioning_audit CHECK literals align with Python.

Migration 030 ships CHECK constraints on
``resource_provisioning_audit``:

* ``mutation_type``  — pipeline entrypoint name(s)
* ``kind``           — ResourceKind value
* ``mode``           — use_existing | create
* ``outcome``        — success | permission_blocked | discord_failed
                       | binding_failed | declined
* ``actor_type``     — actor model

The Python pipeline carries matching ``frozenset``s in
:mod:`services.resource_provisioning`.  This test pins both sides so
a drift on either fails CI before the next migration ships.
"""

from __future__ import annotations

import re
from pathlib import Path

_MIGRATIONS = Path(__file__).resolve().parents[3] / "disbot" / "migrations"
_MIGRATION = _MIGRATIONS / "030_resource_provisioning_audit.sql"
# actor_type was widened to add 'setup_delegate' in migration 069 (Q-0098).
_ACTOR_TYPE_MIGRATION = _MIGRATIONS / "069_setup_delegate_actor_type.sql"


def _read() -> str:
    return _MIGRATION.read_text()


def _extract_in_set(column: str) -> set[str]:
    sql = _read()
    pattern = rf"CHECK\s*\(\s*{column}\s+IN\s*\(([^)]+)\)\s*\)"
    match = re.search(pattern, sql)
    assert match, f"could not locate {column} CHECK constraint in migration 030"
    return {
        tok.strip().strip("'\"") for tok in match.group(1).split(",") if tok.strip()
    }


def _extract_actor_type_set() -> set[str]:
    """Effective actor_type literals, read from migration 069's named CHECK.

    Anchored on the constraint NAME so the two audit tables widened in the same
    migration can't silently diverge.
    """
    sql = _ACTOR_TYPE_MIGRATION.read_text()
    pattern = (
        r"resource_provisioning_audit_actor_type_check\s+CHECK\s*\(\s*actor_type"
        r"\s+IN\s*\(([^)]+)\)"
    )
    match = re.search(pattern, sql)
    assert match, "could not locate resource actor_type CHECK in migration 069"
    return {
        tok.strip().strip("'\"") for tok in match.group(1).split(",") if tok.strip()
    }


def test_mutation_type_literals_match_pipeline():
    from services.resource_provisioning import _ALLOWED_MUTATION_TYPES

    db_check = _extract_in_set("mutation_type")
    python = set(_ALLOWED_MUTATION_TYPES)
    assert db_check == python, (
        "mutation_type drift:\n"
        f"  in Python but not DB CHECK: {sorted(python - db_check)}\n"
        f"  in DB CHECK but not Python: {sorted(db_check - python)}"
    )


def test_kind_literals_match_pipeline():
    from services.resource_provisioning import _ALLOWED_KINDS

    db_check = _extract_in_set("kind")
    python = set(_ALLOWED_KINDS)
    assert db_check == python, (
        "kind drift:\n"
        f"  in Python but not DB CHECK: {sorted(python - db_check)}\n"
        f"  in DB CHECK but not Python: {sorted(db_check - python)}"
    )


def test_mode_literals_match_pipeline():
    from services.resource_provisioning import _ALLOWED_MODES

    db_check = _extract_in_set("mode")
    python = set(_ALLOWED_MODES)
    assert db_check == python, (
        "mode drift:\n"
        f"  in Python but not DB CHECK: {sorted(python - db_check)}\n"
        f"  in DB CHECK but not Python: {sorted(db_check - python)}"
    )


def test_outcome_literals_match_pipeline():
    from services.resource_provisioning import _ALLOWED_OUTCOMES

    db_check = _extract_in_set("outcome")
    python = set(_ALLOWED_OUTCOMES)
    assert db_check == python, (
        "outcome drift:\n"
        f"  in Python but not DB CHECK: {sorted(python - db_check)}\n"
        f"  in DB CHECK but not Python: {sorted(db_check - python)}"
    )


def test_actor_type_literals_match_pipeline():
    from services.resource_provisioning import _ALLOWED_ACTOR_TYPES

    db_check = _extract_actor_type_set()
    python = set(_ALLOWED_ACTOR_TYPES)
    assert db_check == python, (
        "actor_type drift:\n"
        f"  in Python but not DB CHECK: {sorted(python - db_check)}\n"
        f"  in DB CHECK but not Python: {sorted(db_check - python)}\n"
        "Fix: extend the CHECK in migration 069 AND _ALLOWED_ACTOR_TYPES in "
        "services/resource_provisioning.py."
    )


def test_migration_file_exists():
    assert _MIGRATION.exists(), f"migration file missing: {_MIGRATION}"


def _strip_sql_comments(sql: str) -> str:
    """Drop ``--`` line comments before scanning for forbidden statements."""
    out_lines: list[str] = []
    for line in sql.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("--"):
            continue
        if "--" in line:
            line = line.split("--", 1)[0]
        out_lines.append(line)
    return "\n".join(out_lines)


def test_migration_is_forward_only_and_idempotent():
    """Forward-only excludes DROP / DELETE / TRUNCATE / ALTER on
    existing tables.  Idempotency via ``CREATE … IF NOT EXISTS``.
    SQL ``--`` comments are stripped so the rollback note describing
    ``-- Rollback: DROP TABLE ...`` does not trip the check.
    """
    sql = _strip_sql_comments(_read()).upper()
    forbidden = (
        "DROP ",
        "TRUNCATE ",
        "DELETE FROM ",
        "ALTER TABLE SUBSYSTEM_BINDINGS",
        "ALTER TABLE GUILD_SETTINGS",
    )
    for needle in forbidden:
        assert (
            needle not in sql
        ), f"migration 030 contains forbidden destructive statement: {needle!r}"
    assert "CREATE TABLE IF NOT EXISTS" in sql
    assert "CREATE INDEX IF NOT EXISTS" in sql
