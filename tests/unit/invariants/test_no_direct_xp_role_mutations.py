"""XP level-role grants must route through the audited role_automation seam.

The XP listener grants/removes level-threshold roles on level-up. Those member
mutations must go through ``services.role_automation.apply`` (which fires
``audit.action_recorded`` and applies the shared manage-roles / hierarchy
preflight) — **not** a direct ``member.add_roles`` / ``member.remove_roles``
call, which was the one XP-side audit gap (closed: the listener now builds
``Assignment`` rows and calls ``role_automation.apply``).

This is the XP-cog complement to ``test_no_direct_role_mutations.py`` (which
scopes the role cog/views and deliberately leaves member assignment out, noting
that "the automation apply path in services.role_automation is already
audited"). This invariant pins that the XP automation path actually uses it.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_LISTENER = _REPO_ROOT / "disbot" / "cogs" / "xp" / "listener.py"

_FORBIDDEN_MEMBER_METHODS = {"add_roles", "remove_roles"}


def _direct_member_role_calls(tree: ast.AST) -> list[str]:
    found: list[str] = []
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
            continue
        if n.func.attr in _FORBIDDEN_MEMBER_METHODS:
            found.append(f".{n.func.attr}() @ line {n.lineno}")
    return found


def test_xp_listener_routes_role_grants_through_role_automation():
    assert _LISTENER.exists(), "xp listener moved — update this invariant"
    tree = ast.parse(_LISTENER.read_text(), filename=str(_LISTENER))
    violations = _direct_member_role_calls(tree)
    assert not violations, (
        "XP listener must route level-role grants through "
        "services.role_automation.apply (audited), not a direct member role "
        f"mutation. Found: {violations}"
    )
