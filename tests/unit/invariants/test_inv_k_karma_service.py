"""INV-K regression — every karma mutation flows through karma_service.

Static AST scan that fails the build if any production file outside the
service layer touches the karma write primitives directly:

    db.credit_karma / db.increment_given / db.insert_karma_audit
    (and their utils.db.karma.* spellings)

``services.karma_service`` is the only allowed caller — it wraps them
with the anti-abuse checks, the audit-log write, and the EventBus emit.
The read primitives (get_karma, top_karma, karma_rank, recent_grant_count,
grants_given_since) are intentionally NOT contained: the leaderboard
provider and the cog read them freely.

Also scans for inline raw SQL that writes the ``karma`` / ``karma_audit_log``
tables, since a cog could route around the service with a custom INSERT.

Mirrors :mod:`tests.unit.invariants.test_inv_f_economy_service` (INV-F).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

# Files ALLOWED to call the low-level write primitives. Anything else
# must route through services.karma_service.
_ALLOWED_PATHS = {
    _DISBOT / "services" / "karma_service.py",
    _DISBOT / "utils" / "db" / "karma.py",
    _DISBOT / "utils" / "db" / "__init__.py",
    _DISBOT / "utils" / "db" / "pool.py",
}

_FORBIDDEN_NAMES = {
    "credit_karma",
    "increment_given",
    "insert_karma_audit",
}

# Raw SQL that writes the karma tables (read-only SELECTs are fine).
_SQL_WRITE_RE = re.compile(
    r"(INSERT\s+INTO\s+karma\b|UPDATE\s+karma\b|"
    r"INSERT\s+INTO\s+karma_audit_log\b)",
    re.IGNORECASE,
)


def _iter_production_py_files() -> list[Path]:
    return [p for p in _DISBOT.rglob("*.py") if "__pycache__" not in p.parts]


def _direct_calls_to(node: ast.AST, names: set[str]) -> list[str]:
    """Return the dotted-name strings called as ``something.<name>(...)``."""
    found: list[str] = []
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            if n.func.attr in names:
                rcv = n.func.value
                parts: list[str] = []
                while isinstance(rcv, ast.Attribute):
                    parts.append(rcv.attr)
                    rcv = rcv.value
                if isinstance(rcv, ast.Name):
                    parts.append(rcv.id)
                receiver = ".".join(reversed(parts))
                found.append(f"{receiver}.{n.func.attr}")
    return found


def test_no_direct_karma_mutation_outside_service():
    """No production file (other than the service + db primitives) may
    call the karma write primitives directly.
    """
    violations: list[tuple[str, list[str]]] = []
    for path in _iter_production_py_files():
        if path in _ALLOWED_PATHS:
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        calls = _direct_calls_to(tree, _FORBIDDEN_NAMES)
        if calls:
            violations.append((str(path.relative_to(_REPO_ROOT)), calls))
    assert not violations, (
        "INV-K violation: karma mutations outside services.karma_service.\n"
        + "\n".join(f"  {p}: {calls}" for p, calls in violations)
    )


def test_no_raw_sql_writes_to_karma_outside_db_layer():
    """No production file outside utils/db/* may issue raw INSERT/UPDATE
    against the karma tables — the DB layer owns the write SQL.
    """
    violations: list[str] = []
    for path in _iter_production_py_files():
        rel = path.relative_to(_REPO_ROOT)
        if str(rel).startswith("disbot/utils/db/"):
            continue
        if path.suffix != ".py":
            continue
        src = path.read_text()
        for match in _SQL_WRITE_RE.finditer(src):
            violations.append(
                f"{rel}: matched raw SQL fragment {match.group(0)!r}",
            )
    assert not violations, (
        "INV-K violation: raw SQL karma writes outside utils/db/:\n"
        + "\n".join(violations)
    )


@pytest.mark.parametrize(
    "allowed_path",
    sorted(p.relative_to(_REPO_ROOT) for p in _ALLOWED_PATHS),
)
def test_allow_list_files_actually_exist(allowed_path):
    """Keep the allowlist honest — a drifted path weakens the scan silently."""
    p = _REPO_ROOT / allowed_path
    assert p.exists(), f"INV-K allowlist references missing file: {allowed_path}"
