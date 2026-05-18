"""S4 invariant — settings_mutation_audit CHECK literals align with Python.

Migration 029 ships CHECK constraints on
``settings_mutation_audit``:

* ``mutation_type``  — pipeline entrypoint name(s)
* ``actor_type``     — actor model

The Python pipeline carries matching ``frozenset``s in
:mod:`services.settings_mutation`.  This test pins both sides so a
drift on either fails CI before the next migration ships.
"""

from __future__ import annotations

import re
from pathlib import Path

_MIGRATION = (
    Path(__file__).resolve().parents[3]
    / "disbot"
    / "migrations"
    / "029_settings_mutation_audit.sql"
)


def _read() -> str:
    return _MIGRATION.read_text()


def _extract_in_set(column: str) -> set[str]:
    sql = _read()
    pattern = rf"CHECK\s*\(\s*{column}\s+IN\s*\(([^)]+)\)\s*\)"
    match = re.search(pattern, sql)
    assert match, f"could not locate {column} CHECK constraint in migration 029"
    return {
        tok.strip().strip("'\"") for tok in match.group(1).split(",") if tok.strip()
    }


def test_mutation_type_literals_match_pipeline():
    """``mutation_type`` CHECK matches
    :data:`services.settings_mutation._ALLOWED_MUTATION_TYPES`.
    """
    from services.settings_mutation import _ALLOWED_MUTATION_TYPES

    db_check = _extract_in_set("mutation_type")
    python = set(_ALLOWED_MUTATION_TYPES)
    assert db_check == python, (
        "mutation_type drift:\n"
        f"  in Python but not DB CHECK: {sorted(python - db_check)}\n"
        f"  in DB CHECK but not Python: {sorted(db_check - python)}\n"
        "Fix: extend the CHECK constraint via a new migration AND "
        "update _ALLOWED_MUTATION_TYPES in services/settings_mutation.py."
    )


def test_actor_type_literals_match_pipeline_allowed_set():
    """``actor_type`` CHECK matches
    :data:`services.settings_mutation._ALLOWED_ACTOR_TYPES`.
    """
    from services.settings_mutation import _ALLOWED_ACTOR_TYPES

    db_check = _extract_in_set("actor_type")
    python = set(_ALLOWED_ACTOR_TYPES)
    assert db_check == python, (
        "actor_type drift:\n"
        f"  in Python but not DB CHECK: {sorted(python - db_check)}\n"
        f"  in DB CHECK but not Python: {sorted(db_check - python)}"
    )


def test_migration_file_exists():
    """Sanity: the migration referenced by this alignment test exists."""
    assert _MIGRATION.exists(), f"migration file missing: {_MIGRATION}"


def _strip_sql_comments(sql: str) -> str:
    """Drop ``--`` line comments before scanning for forbidden statements."""
    out_lines: list[str] = []
    for line in sql.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("--"):
            continue
        # Inline trailing comment.
        if "--" in line:
            line = line.split("--", 1)[0]
        out_lines.append(line)
    return "\n".join(out_lines)


def test_migration_is_forward_only_and_idempotent():
    """The migration must not contain destructive statements.

    Idempotency is provided by ``CREATE TABLE IF NOT EXISTS`` and
    ``CREATE INDEX IF NOT EXISTS``.  Forward-only excludes DROP /
    DELETE / TRUNCATE / ALTER on existing tables.  SQL ``--``
    comments are stripped before scanning so a comment that
    *describes* the rollback (``-- Rollback: DROP TABLE ...``) does
    not trip the check.
    """
    sql = _strip_sql_comments(_read()).upper()
    forbidden = ("DROP ", "TRUNCATE ", "DELETE FROM ", "ALTER TABLE GUILD_SETTINGS")
    for needle in forbidden:
        assert (
            needle not in sql
        ), f"migration 029 contains forbidden destructive statement: {needle!r}"
    # Idempotency markers must be on real (non-comment) statements.
    assert "CREATE TABLE IF NOT EXISTS" in sql
    assert "CREATE INDEX IF NOT EXISTS" in sql
