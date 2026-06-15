"""INV-F regression — every economy mutation flows through economy_service.

Static AST scan that fails the build if any production file outside the
service layer touches the balance primitives directly:

    db.add_coins / db.set_coins / utils.db.economy.add_coins / .set_coins

The economy_service module is the only allowed caller of those
primitives (it wraps them with audit-log writes and EventBus emits).

Also scans for inline raw SQL that writes the ``xp.coins`` column,
since a cog could route around economy_service by executing a custom
UPDATE.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

# Files that are ALLOWED to call the low-level primitives.  Anything
# else must route through services.economy_service.
_ALLOWED_PATHS = {
    _DISBOT / "services" / "economy_service.py",
    _DISBOT / "utils" / "db" / "economy.py",
    _DISBOT / "utils" / "db" / "__init__.py",
    _DISBOT / "utils" / "db" / "pool.py",
}

_FORBIDDEN_NAMES = {
    "add_coins",
    "set_coins",
    # RS01 transaction-aware primitives — same containment as add/set:
    # only economy_service (debit_in_txn / credit_in_txn) and the DB
    # layer itself may touch them.
    "try_debit_coins",
    "credit_coins",
    "insert_economy_audit",
}

# Raw SQL that writes the xp.coins column or the economy table.  We
# accept SELECTs (read-only) and any reference inside utils/db/*.
_SQL_WRITE_RE = re.compile(
    r"(UPDATE\s+xp\b|INSERT\s+INTO\s+xp\s*\([^)]*\bcoins\b|" r"UPDATE\s+economy\b)",
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
                # Reconstruct the receiver to surface "db.add_coins" etc.
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


def test_no_direct_balance_mutation_outside_service():
    """No production file (other than the service + db primitives) may
    call ``add_coins`` / ``set_coins`` directly.
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
        "INV-F violation: balance mutations outside services.economy_service.\n"
        + "\n".join(f"  {p}: {calls}" for p, calls in violations)
    )


def test_no_raw_sql_writes_to_coins_outside_db_or_service_layer():
    """No production file outside utils/db/* or services/economy_service.py
    may issue raw UPDATE/INSERT against the xp.coins column or the economy
    table.  The service layer owns the atomic transfer SQL legitimately.
    """
    violations: list[str] = []
    allowed_sql_writers = {
        _DISBOT / "services" / "economy_service.py",
    }
    for path in _iter_production_py_files():
        rel = path.relative_to(_REPO_ROOT)
        # The DB layer is allowed to write directly; that's its purpose.
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
        "INV-F violation: raw SQL balance writes outside utils/db/ "
        "or services/economy_service.py:\n" + "\n".join(violations)
    )


@pytest.mark.parametrize(
    "allowed_path",
    sorted(p.relative_to(_REPO_ROOT) for p in _ALLOWED_PATHS),
)
def test_allow_list_files_actually_exist(allowed_path):
    """If the allowlist drifts from the actual filesystem the test
    weakens silently — keep the list honest.
    """
    p = _REPO_ROOT / allowed_path
    assert p.exists(), f"INV-F allowlist references missing file: {allowed_path}"
