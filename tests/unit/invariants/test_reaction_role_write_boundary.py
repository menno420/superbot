"""Audit-F6 fence — every reaction-role-overhaul write flows through its service.

The reaction-role overhaul (11 PRs) shipped the subsystem's newest, largest
mutation surface with an audited seam but without the ratchet step the older
seams got (chain, mining, thresholds, moderation — "enforce, don't exhort",
Q-0132/Q-0194; evidence: ``docs/analysis/server-management-audit-2026-07-08.md``
finding F6). This suite pins the five overhaul tables

    role_menus · role_menu_options · reaction_role_message_modes ·
    role_grants · role_menu_pickup_stats

to their two audited writers: ``services/reaction_role_service.py`` (menus,
options, message modes, pickup stats) and ``services/role_grants_service.py``
(temp-role grants). No cog, view, or other service may call the DB write
primitives directly.

AST scan modeled on ``test_chain_write_boundary.py`` with the
``test_mining_write_boundary.py`` receiver tier: names unique to this DB layer
are forbidden on ANY receiver (and as bare ``from``-imported calls); names that
collide with other subsystems (the service re-exports ``create_menu`` /
``delete_menu`` / …, ``treasury_cog.grant``, ``session_manager.remove``, the
ten per-domain ``delete_for_guild`` teardown helpers) are forbidden only on a
DB-ish receiver. Reads (``get_*`` / ``list_*``) stay free — e.g. the
diagnostics panel's ``get_pickup_stats`` read is legitimate.

Scans ALL of ``disbot/`` except the two services, the owning DB modules, and
``guild_lifecycle.py`` (the sanctioned INV-I teardown carve-out the audit
allowlists), so a new writer can't appear in any layer unnoticed.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

# The only modules allowed to reference the write primitives: the owners
# (define them), the two audited services (the sole callers), and the guild
# teardown (audit-F6 allowlist — ``_teardown_role_menus`` etc. purge departed
# guilds' rows per architecture INV-I).
_ALLOWED_FILES = {
    _DISBOT / "services" / "reaction_role_service.py",
    _DISBOT / "services" / "role_grants_service.py",
    _DISBOT / "utils" / "db" / "role_menus.py",
    _DISBOT / "utils" / "db" / "role_grants.py",
    _DISBOT / "utils" / "db" / "roles.py",
    _DISBOT / "guild_lifecycle.py",
}

# Names unique to this DB layer (one ``def`` in all of disbot/) — forbidden on
# ANY receiver, and as bare from-imported calls.
_FORBIDDEN_ANY_RECEIVER = {
    # role_menu_options (PR 2 builder writes the whole list transactionally)
    "replace_options",
    # role_menu_pickup_stats (PR 5 analytics counters + teardown)
    "record_pickup",
    "record_removal",
    "delete_pickup_stats_for_guild",
    # role_grants
    "delete_grant",
    # reaction_role_message_modes (overhaul PR 3, owned by utils/db/roles.py)
    "set_reaction_message_mode",
    "clear_reaction_message_mode",
    "delete_reaction_modes_for_guild",
}

# Names that collide with other subsystems — the service wraps the menu CRUD
# under the SAME names (``reaction_role_service.create_menu`` is the legit
# call), ``grant``/``remove`` exist on treasury/session-manager, and every
# domain DB module has a ``delete_for_guild`` — forbidden only on a DB-ish
# receiver.
_FORBIDDEN_DB_RECEIVER = {
    "create_menu",
    "update_menu",
    "delete_menu",
    "set_menu_message",
    "set_menu_location",
    "add_option",
    "remove_option",
    "grant",
    "remove",
    "delete_for_guild",
}

_DB_RECEIVERS = {
    "db",
    "pool",
    "role_menus",
    "menus_db",
    "role_grants",
    "grants_db",
    "roles",
    "roles_db",
}


def _receiver_leaf(node: ast.Attribute) -> str:
    """The attribute closest to the call, e.g. ``role_menus`` in
    ``utils.db.role_menus.create_menu``."""
    leaf = node.value
    if isinstance(leaf, ast.Attribute):
        return leaf.attr
    if isinstance(leaf, ast.Name):
        return leaf.id
    return ""


def _write_calls(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    found: list[str] = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        if isinstance(n.func, ast.Attribute):
            name = n.func.attr
            if name in _FORBIDDEN_ANY_RECEIVER:
                found.append(f"{name} (line {n.lineno})")
            elif name in _FORBIDDEN_DB_RECEIVER:
                if _receiver_leaf(n.func) in _DB_RECEIVERS:
                    found.append(f"{name} (line {n.lineno})")
        elif isinstance(n.func, ast.Name) and n.func.id in _FORBIDDEN_ANY_RECEIVER:
            # ``from utils.db.role_menus import replace_options`` style — the
            # guild_lifecycle teardown pattern, legit only in allowed files.
            found.append(f"{n.func.id} (line {n.lineno}, bare call)")
    return found


def test_no_direct_reaction_role_writes_outside_services():
    violations: list[tuple[str, list[str]]] = []
    for path in sorted(_DISBOT.rglob("*.py")):
        if "__pycache__" in path.parts or path in _ALLOWED_FILES:
            continue
        calls = _write_calls(path)
        if calls:
            violations.append((str(path.relative_to(_REPO_ROOT)), calls))
    assert not violations, (
        "Audit-F6 violation: direct reaction-role-table writes outside "
        "services/reaction_role_service.py / services/role_grants_service.py "
        "(route through the audited service seam):\n"
        + "\n".join(f"  {p}: {calls}" for p, calls in violations)
    )


def test_audited_reaction_role_seams_exist():
    """Positive check — the canonical seams exist and emit the audit
    companion (not silent writes)."""
    src = (_DISBOT / "services" / "reaction_role_service.py").read_text()
    assert "async def create_menu(" in src
    assert "async def update_menu(" in src
    assert "async def delete_menu(" in src
    assert "async def set_message_mode(" in src
    assert "async def toggle_role(" in src
    assert "emit_audit_action(" in src

    src = (_DISBOT / "services" / "role_grants_service.py").read_text()
    assert "async def grant_temp_role(" in src
    assert "async def sweep_expired(" in src
    assert "emit_audit_action(" in src
