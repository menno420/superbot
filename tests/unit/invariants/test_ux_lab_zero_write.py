"""UX Lab zero-write fence — the lab must never gain a mutation path.

The UX Lab is a gallery of *fake* interactions (design decision, UX Lab plan
§0/§7): no DB access, no service calls, no governance reads, no audit
emissions — its only side effects are Discord messages in the invoking
channel. This AST fence makes the property structural: the moment any
ux-lab module imports a write-capable layer, CI names the file and line.

Inverse of the ``test_game_wager_write_boundary`` precedent: that fence
forces writes *through* a seam; this one forbids the seam entirely.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

# Every module that makes up the lab. New wing files are picked up
# automatically via the package globs.
_UX_LAB_PATHS = (
    _DISBOT / "cogs" / "ux_lab_cog.py",
    *sorted((_DISBOT / "views" / "ux_lab").glob("*.py")),
    *sorted((_DISBOT / "utils" / "ux_patterns").glob("*.py")),
)

# Top-level packages/modules the lab may never import (module-level OR
# lazy/function-body — ast.walk sees both).
_FORBIDDEN_IMPORT_ROOTS = ("services", "governance", "utils.db")

# Attribute names whose mere call is a mutation signal regardless of receiver.
_FORBIDDEN_CALLS = {"emit_audit_action", "execute", "executemany", "fetchrow"}


def _violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(_FORBIDDEN_IMPORT_ROOTS):
                    found.append(f"import {alias.name} (line {node.lineno})")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.startswith(_FORBIDDEN_IMPORT_ROOTS) or (
                mod == "utils" and any(a.name == "db" for a in node.names)
            ):
                found.append(f"from {mod} import … (line {node.lineno})")
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in _FORBIDDEN_CALLS
        ):
            found.append(f"call .{node.func.attr}(…) (line {node.lineno})")
    return found


def test_ux_lab_files_exist():
    """The fence must actually cover the lab (guards against path drift)."""
    assert (_DISBOT / "cogs" / "ux_lab_cog.py").exists()
    assert (_DISBOT / "views" / "ux_lab" / "home.py").exists()
    assert (_DISBOT / "utils" / "ux_patterns" / "registry.py").exists()
    assert len(list(_UX_LAB_PATHS)) >= 8


def test_ux_lab_never_writes():
    violations: list[tuple[str, list[str]]] = []
    for path in _UX_LAB_PATHS:
        if path.name == "__pycache__":
            continue
        found = _violations(path)
        if found:
            violations.append((str(path.relative_to(_REPO_ROOT)), found))
    assert not violations, (
        "UX Lab zero-write fence violated — the lab must stay a fake-only "
        "gallery (UX Lab plan §0). Remove the import/call or build the "
        "feature outside the lab:\n"
        + "\n".join(f"  {p}: {found}" for p, found in violations)
    )
