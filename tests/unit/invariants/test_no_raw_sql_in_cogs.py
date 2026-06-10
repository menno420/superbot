"""RS08 fence — no inline SQL in the cog/view layers.

Raw SQL belongs to ``utils/db/`` (the table's owning module); cogs and
views compose those read models and render. The 2026-06-10
runtime/services map (FIND-RS08) found the diagnostic embed builders
carrying their own SQL (`runtime_sessions` / `panel_anchors` /
`pg_tables` aggregates), and ``cogs/xp/_helpers.py`` still re-derived
ranks inline after ``services/rank_providers.py`` centralised that
logic. Those were the last inline queries in either layer — this
invariant keeps the count at zero so the drift class cannot recur
(the Community Spotlight review found the same class in 2026-06-09).

Shape-targeted AST scan: a call to a fetch/execute-style method whose
first positional argument is a string literal that starts with a SQL
keyword. Building SQL in a cog and passing it via a variable would slip
past this — that is fine; the fence targets the observed drift shape,
not adversarial evasion.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCANNED_DIRS = (
    _REPO_ROOT / "disbot" / "cogs",
    _REPO_ROOT / "disbot" / "views",
)

_QUERY_METHODS = {
    "fetchall",
    "fetchone",
    "fetchrow",
    "fetch",
    "fetchval",
    "execute",
    "executemany",
}

_SQL_KEYWORDS = (
    "SELECT",
    "INSERT",
    "UPDATE",
    "DELETE",
    "WITH",
    "CREATE",
    "ALTER",
    "DROP",
    "TRUNCATE",
)


def _is_sql_literal(node: ast.expr) -> bool:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        text = node.value.lstrip().upper()
        return text.startswith(_SQL_KEYWORDS)
    if isinstance(node, ast.JoinedStr):  # f-string SQL is doubly forbidden
        head = node.values[0] if node.values else None
        return (
            isinstance(head, ast.Constant)
            and isinstance(head.value, str)
            and head.value.lstrip().upper().startswith(_SQL_KEYWORDS)
        )
    return False


def _inline_sql_calls(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    found: list[str] = []
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
            continue
        if n.func.attr not in _QUERY_METHODS or not n.args:
            continue
        if _is_sql_literal(n.args[0]):
            found.append(f"{n.func.attr} (line {n.lineno})")
    return found


def test_no_inline_sql_in_cogs_or_views():
    violations: list[tuple[str, list[str]]] = []
    for base in _SCANNED_DIRS:
        for path in sorted(base.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            calls = _inline_sql_calls(path)
            if calls:
                violations.append((str(path.relative_to(_REPO_ROOT)), calls))
    assert not violations, (
        "Inline SQL in a cog/view (RS08): move the query into the owning "
        "utils/db module (or an existing service read model) and call that:\n"
        + "\n".join(f"  {p}: {calls}" for p, calls in violations)
    )
