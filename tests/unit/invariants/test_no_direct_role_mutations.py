"""Role-lifecycle convergence invariant (server-management PR5).

The role command + view surface (``cogs/role_cog.py`` and ``views/roles/*``)
must route role *object* mutations through
``services.role_lifecycle_service.RoleLifecycleService`` — no direct
``guild.create_role`` / ``role.delete()`` / ``role.edit()`` remain.

Scope notes:

* ``create_role`` is forbidden by method name regardless of receiver.
* ``.delete()`` / ``.edit()`` are pinned, **except** when the receiver is a
  *message* (``self.message`` / ``self.parent.message`` / ``interaction.message``)
  — that is the legitimate panel-refresh pattern, not a role mutation, so it is
  excluded by receiver tail.
* **Member assignment** (``member.add_roles`` / ``remove_roles`` for reaction
  roles and time/XP automation) is out of scope for PR5 and is NOT pinned here;
  the automation apply path in ``services.role_automation`` is already audited.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

_SCANNED_FILES = (_DISBOT / "cogs" / "role_cog.py",)
_SCANNED_DIRS = (_DISBOT / "views" / "roles",)

# Mutations routed through RoleLifecycleService in PR5.
_FORBIDDEN_CREATE = {"create_role"}
_FORBIDDEN_ROLE_METHODS = {"delete", "edit"}
# Receiver last-segment names that denote a *message*, not a role — the legit
# panel-refresh pattern (``self.message.edit`` / ``interaction.message.edit`` …).
_MESSAGE_RECEIVER_TAILS = {"message"}


def _role_surface_files() -> list[Path]:
    files: list[Path] = []
    for d in _SCANNED_DIRS:
        if d.is_dir():
            files.extend(p for p in d.rglob("*.py") if "__pycache__" not in p.parts)
    files.extend(p for p in _SCANNED_FILES if p.exists())
    return sorted(set(files))


def _receiver_tail(node: ast.expr) -> str:
    """Last segment of a call receiver (``self.parent.message`` → ``message``)."""
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _violations_in(tree: ast.AST) -> list[str]:
    found: list[str] = []
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
            continue
        attr = n.func.attr
        if attr in _FORBIDDEN_CREATE:
            found.append(f".{attr}() @ line {n.lineno}")
        elif attr in _FORBIDDEN_ROLE_METHODS:
            if _receiver_tail(n.func.value) not in _MESSAGE_RECEIVER_TAILS:
                found.append(f".{attr}() @ line {n.lineno}")
    return found


def test_role_surfaces_route_through_service():
    """No role adapter may create/edit/delete a role directly."""
    violations: list[tuple[str, list[str]]] = []
    for path in _role_surface_files():
        tree = ast.parse(path.read_text(), filename=str(path))
        calls = _violations_in(tree)
        if calls:
            violations.append((str(path.relative_to(_REPO_ROOT)), calls))
    assert not violations, (
        "Role-lifecycle violation: direct role create/edit/delete outside "
        "services.role_lifecycle_service.RoleLifecycleService.\n"
        + "\n".join(f"  {p}: {calls}" for p, calls in violations)
    )


def test_scanned_surfaces_exist():
    """Keep the scan honest — if the surfaces move, update this invariant."""
    assert (
        _role_surface_files()
    ), "no role surface files found to scan — did the layout change?"


def test_role_surface_wires_the_service():
    """Positive check — the role cog actually imports the service it must use."""
    src = (_DISBOT / "cogs" / "role_cog.py").read_text()
    assert "RoleLifecycleService" in src
