"""INV-G regression — every XP mutation flows through xp_service.

Static AST scan that fails the build if any production file outside
the service layer touches the XP primitives directly:

    db.add_xp / db.delete_xp / db.set_imported_xp
    (or the utils.db.xp.* equivalents)

The xp_service module is the only allowed caller of those primitives.
``add_xp`` / ``delete_xp`` are wrapped with EventBus emits (EVT_XP_AWARDED /
EVT_LEVEL_UP / EVT_XP_RESET); ``set_imported_xp`` is the raise-only
bot-to-bot migration write, wrapped by ``xp_service.import_level`` so the
``xp`` column is still only ever written from one place.

Also scans for inline raw SQL that writes or deletes the ``xp`` table,
since a cog could route around xp_service by executing custom SQL.

Mirrors INV-F (test_inv_f_economy_service.py).  No cog or view may
write XP directly: every grant or reset routes through the service.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

# Files that are ALLOWED to call the low-level XP primitives.
# Anything else must route through services.xp_service.
_ALLOWED_PATHS = {
    _DISBOT / "services" / "xp_service.py",
    _DISBOT / "utils" / "db" / "xp.py",
    _DISBOT / "utils" / "db" / "__init__.py",
    _DISBOT / "utils" / "db" / "pool.py",
}

_FORBIDDEN_NAMES = {"add_xp", "delete_xp", "set_imported_xp"}

# Raw SQL that writes the ``xp.xp`` integer column or deletes from
# the xp table.  The xp table is shared with the coins column
# (economy_service owns those writes legitimately under INV-F), so
# we match only:
#   - DELETE FROM xp           — wipes the row entirely
#   - UPDATE xp SET xp=        — direct XP-column write
#   - INSERT INTO xp (... xp ...)  — insert that includes the xp column
# SELECTs are read-only and allowed; any reference inside utils/db/*
# is allowed.
_SQL_WRITE_RE = re.compile(
    r"(DELETE\s+FROM\s+xp\b"
    r"|UPDATE\s+xp\s+SET\s+xp\b"
    r"|INSERT\s+INTO\s+xp\s*\([^)]*\bxp\b)",
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


def test_no_direct_xp_mutation_outside_service():
    """No production file (other than the service + db primitives + the
    grandfathered xp_cog.on_message path) may call ``add_xp`` /
    ``delete_xp`` directly.
    """
    violations: list[tuple[str, list[str]]] = []
    for path in _iter_production_py_files():
        if path in _ALLOWED_PATHS:
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        calls = _direct_calls_to(tree, _FORBIDDEN_NAMES)
        if calls:
            violations.append((str(path.relative_to(_REPO_ROOT)), calls))
    assert (
        not violations
    ), "INV-G violation: XP mutations outside services.xp_service.\n" + "\n".join(
        f"  {p}: {calls}" for p, calls in violations
    )


def test_no_raw_sql_writes_to_xp_outside_db_or_service_layer():
    """No production file outside utils/db/* or services/xp_service.py
    may issue raw UPDATE/INSERT/DELETE against the xp table.
    """
    violations: list[str] = []
    allowed_sql_writers = {
        _DISBOT / "services" / "xp_service.py",
    }
    for path in _iter_production_py_files():
        rel = path.relative_to(_REPO_ROOT)
        if str(rel).startswith("disbot/utils/db/"):
            continue
        if path in allowed_sql_writers:
            continue
        if path.suffix != ".py":
            continue
        src = path.read_text()
        for match in _SQL_WRITE_RE.finditer(src):
            violations.append(
                f"{rel}: matched raw SQL fragment {match.group(0)!r}",
            )
    assert not violations, (
        "INV-G violation: raw SQL xp writes outside utils/db/ "
        "or services/xp_service.py:\n" + "\n".join(violations)
    )


@pytest.mark.parametrize(
    "allowed_path",
    sorted(p.relative_to(_REPO_ROOT) for p in _ALLOWED_PATHS),
)
def test_allow_list_files_actually_exist(allowed_path):
    """If the allowlist drifts from the filesystem the test weakens
    silently — keep the list honest.
    """
    p = _REPO_ROOT / allowed_path
    assert p.exists(), f"INV-G allowlist references missing file: {allowed_path}"
