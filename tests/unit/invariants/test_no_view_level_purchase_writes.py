"""RS01 ratchet — no view may write purchase legs directly.

The shop previously debited coins and granted the item from the view
callbacks as two separately-committed legs (FIND-RS01).  All purchase
writes now flow through ``services/shop_purchase_workflow.py``; this AST
net keeps any future view from reintroducing the pattern.

Receiver-aware on purpose: ``add_item`` is also ``discord.ui.View.add_item``
(component attach), so it is only flagged when called on a DB-ish receiver
(``db`` / ``…​.db`` / ``inventory`` / ``pool``).  The transaction-leg names
are unique to the DB layer and are flagged on any receiver.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_VIEWS = _REPO_ROOT / "disbot" / "views"

# Unique DB-layer names — forbidden in views on ANY receiver.
_FORBIDDEN_ANY_RECEIVER = {
    "try_grant_unique_item",
    "try_debit_coins",
    "credit_coins",
    "insert_economy_audit",
}

# Names that collide with discord.py APIs — forbidden only on a DB-ish
# receiver (``self.add_item(button)`` is legitimate view code).
_FORBIDDEN_DB_RECEIVER = {"add_item"}

_DB_RECEIVERS = {"db", "inventory", "economy", "pool"}


def _receiver_dotted(node: ast.Attribute) -> str:
    parts: list[str] = []
    rcv: ast.expr = node.value
    while isinstance(rcv, ast.Attribute):
        parts.append(rcv.attr)
        rcv = rcv.value
    if isinstance(rcv, ast.Name):
        parts.append(rcv.id)
    return ".".join(reversed(parts))


def _violations_in(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    found: list[str] = []
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
            continue
        name = n.func.attr
        receiver = _receiver_dotted(n.func)
        leaf = receiver.rsplit(".", 1)[-1] if receiver else ""
        if name in _FORBIDDEN_ANY_RECEIVER:
            found.append(f"{receiver}.{name} (line {n.lineno})")
        elif name in _FORBIDDEN_DB_RECEIVER and leaf in _DB_RECEIVERS:
            found.append(f"{receiver}.{name} (line {n.lineno})")
    return found


def test_no_purchase_write_primitives_called_from_views():
    violations: list[tuple[str, list[str]]] = []
    for path in sorted(_VIEWS.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        calls = _violations_in(path)
        if calls:
            violations.append((str(path.relative_to(_REPO_ROOT)), calls))
    assert not violations, (
        "RS01 violation: purchase-leg writes from view code — route through "
        "services/shop_purchase_workflow.py (Q-0071):\n"
        + "\n".join(f"  {p}: {calls}" for p, calls in violations)
    )
