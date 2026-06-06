"""INV — every persistent health-finding write flows through the sole writer.

Static AST scan (mirrors ``test_inv_f_economy_service.py``): only
``services.health_findings_service`` and its DB primitive layer
(``utils.db.health_findings``) may call the write primitives
(``upsert_finding`` / ``prune_expired`` / ``roll_up_to_aggregates``), and no
other production file may issue raw SQL writes to the
``operational_health_findings*`` tables.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

# Files ALLOWED to call the write primitives. Everything else must route
# through services.health_findings_service.
_ALLOWED_PATHS = {
    _DISBOT / "services" / "health_findings_service.py",
    _DISBOT / "utils" / "db" / "health_findings.py",
    _DISBOT / "utils" / "db" / "__init__.py",
    _DISBOT / "utils" / "db" / "pool.py",
}

_FORBIDDEN_NAMES = {"upsert_finding", "prune_expired", "roll_up_to_aggregates"}

# Raw SQL writes to the findings tables (SELECTs are read-only and allowed).
_SQL_WRITE_RE = re.compile(
    r"((INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+operational_health_finding)",
    re.IGNORECASE,
)


def _iter_production_py_files() -> list[Path]:
    return [p for p in _DISBOT.rglob("*.py") if "__pycache__" not in p.parts]


def _direct_calls_to(node: ast.AST, names: set[str]) -> list[str]:
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


def test_no_direct_finding_writes_outside_service() -> None:
    violations: list[tuple[str, list[str]]] = []
    for path in _iter_production_py_files():
        if path in _ALLOWED_PATHS:
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        calls = _direct_calls_to(tree, _FORBIDDEN_NAMES)
        if calls:
            violations.append((str(path.relative_to(_REPO_ROOT)), calls))
    assert not violations, (
        "Persistent health-finding writes outside health_findings_service:\n"
        + "\n".join(f"  {p}: {calls}" for p, calls in violations)
    )


def test_no_raw_sql_finding_writes_outside_db_layer() -> None:
    violations: list[str] = []
    for path in _iter_production_py_files():
        rel = path.relative_to(_REPO_ROOT)
        if str(rel).startswith("disbot/utils/db/"):
            continue
        for match in _SQL_WRITE_RE.finditer(path.read_text()):
            violations.append(f"{rel}: matched raw SQL fragment {match.group(0)!r}")
    assert not violations, (
        "Raw SQL writes to operational_health_finding* outside utils/db/:\n"
        + "\n".join(violations)
    )


@pytest.mark.parametrize(
    "allowed_path",
    sorted(p.relative_to(_REPO_ROOT) for p in _ALLOWED_PATHS),
)
def test_allow_list_files_actually_exist(allowed_path: Path) -> None:
    p = _REPO_ROOT / allowed_path
    assert p.exists(), f"allowlist references missing file: {allowed_path}"
