"""Cog-routing writer-convergence invariant (consolidated plan Batch 3, RS03).

``services.command_routing.set_policy`` is the canonical mutation owner for
``command_routing_policy`` rows: it reads the old row, writes, emits the
``audit.action_recorded`` companion with the real previous value, and returns
a typed ``RoutingMutationResult``.  A caller that imports the
``utils.db.command_routing`` primitives directly can write silently (no audit,
no previous state) — the exact drift FIND-RS03 documented in the setup
dispatcher, which used to own the routing audit itself with
``prev_value=None``.

This invariant fences the primitives at the **import** level: only the
service seam may import ``utils.db.command_routing``.  (An import fence is
the right shape here — unlike the role-threshold primitives, the routing
module is consumed as a module object (``from utils.db import
command_routing as db``), and its ``set_one``/``get_one`` names are too
generic for a repo-wide attribute-call scan.)
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

# The canonical seam — the ONLY module allowed to import the DB primitives.
_ALLOWED_IMPORTERS = frozenset({"services/command_routing.py"})


def _imports_routing_db(tree: ast.AST) -> bool:
    """True when the module imports ``utils.db.command_routing`` in any form."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(a.name == "utils.db.command_routing" for a in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if node.module == "utils.db.command_routing":
                return True
            if node.module == "utils.db" and any(
                a.name == "command_routing" for a in node.names
            ):
                return True
    return False


def _routing_db_importers() -> set[str]:
    out: set[str] = set()
    for path in _DISBOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        rel = path.relative_to(_DISBOT).as_posix()
        if rel == "utils/db/command_routing.py":
            continue  # the primitive module itself
        tree = ast.parse(path.read_text(), filename=str(path))
        if _imports_routing_db(tree):
            out.add(rel)
    return out


def test_only_the_routing_service_imports_the_db_primitives():
    importers = _routing_db_importers()
    drift = importers - _ALLOWED_IMPORTERS
    assert not drift, (
        "Direct import(s) of utils.db.command_routing outside the canonical "
        "seam — route routing writes through "
        "services.command_routing.set_policy (it owns the old-value read, "
        f"audit emission, and the typed result): {sorted(drift)}"
    )
    # Positive check: the seam itself still consumes the primitives, so the
    # scan is alive (a rename/move would silently empty it otherwise).
    assert "services/command_routing.py" in importers


def test_routing_mutation_seam_shape():
    """The seam owns old-value read + audit emit + typed result."""
    src = (_DISBOT / "services" / "command_routing.py").read_text()
    assert "class RoutingMutationResult" in src
    assert "old_enabled" in src
    assert "emit_audit_action(" in src
