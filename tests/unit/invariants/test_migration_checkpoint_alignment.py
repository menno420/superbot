"""Phase 2 PR-5 invariant — migration_checkpoint status literals align.

Migration 026 ships a CHECK constraint on
``platform_migration_checkpoints.status``.  The Python module
:mod:`utils.db.platform_migration_checkpoints` carries the matching
:data:`KNOWN_STATUSES` set; an extension on one side without the
other would either let an INSERT fail at runtime (Python writes a
value the DB rejects) or let an operator INSERT a value Python never
recognises.
"""

from __future__ import annotations

import re
from pathlib import Path

_MIGRATION = (
    Path(__file__).resolve().parents[3]
    / "disbot"
    / "migrations"
    / "026_platform_migration_checkpoints.sql"
)


def _extract_status_literals() -> set[str]:
    sql = _MIGRATION.read_text()
    match = re.search(
        r"CHECK\s*\(\s*status\s+IN\s*\(([^)]+)\)\s*\)",
        sql,
        re.DOTALL,
    )
    assert match, "could not locate status CHECK constraint in migration 026"
    return {
        token.strip().strip("'\"")
        for token in match.group(1).split(",")
        if token.strip()
    }


def test_status_literals_match_python_known_statuses():
    """``status`` CHECK matches ``KNOWN_STATUSES`` exactly."""
    from utils.db.platform_migration_checkpoints import KNOWN_STATUSES

    db_check = _extract_status_literals()
    python = set(KNOWN_STATUSES)
    assert db_check == python, (
        "platform_migration_checkpoints status drift.\n"
        f"  in Python but not DB CHECK: {sorted(python - db_check)}\n"
        f"  in DB CHECK but not Python: {sorted(db_check - python)}\n"
        "Fix: extend the CHECK constraint via a new migration AND "
        "update KNOWN_STATUSES in "
        "utils/db/platform_migration_checkpoints.py.",
    )
