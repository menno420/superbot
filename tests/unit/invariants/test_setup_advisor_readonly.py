"""Invariant: the AI setup-advisor review path is read-only.

``services.setup_advisor_review`` powers the optional "Ask AI to review"
action on Final Review.  Because it is AI-adjacent, mutation safety is
non-negotiable (plan §9 / §D3): it must never write to the DB, call a
mutation pipeline, create/edit/delete Discord resources, or touch the
setup draft / session.  It reads a snapshot and returns advisory text.

This is an AST-level guard over the whole module (it is small and
entirely advisory), mirroring
``tests/unit/invariants/test_setup_preflight_readonly.py``.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MODULE = _REPO_ROOT / "disbot" / "services" / "setup_advisor_review.py"

# Mutation-pipeline entry points + raw DB write/read primitives.
_FORBIDDEN_MUTATION = {
    "set_binding",
    "clear_binding",
    "set_setting",
    "set_participation",
    "set_subscription",
    "set_preference",
    "set_visibility",
    "apply_cleanup_policy",
    "set_cog_enabled",
    "add_rule",
    "set_enabled",
    "create_resource",
    "provision",
    "set_flag_state",
    "execute",
    "executemany",
    "fetch",
    "fetchrow",
    "fetchval",
    "apply_operations",
    "append",  # setup_draft.append — staging is a mutation
    "replace_recommended_for_section",
    "clear",  # setup_draft.clear
    "mark_complete",
    "mark_in_progress",
    "start_session",
}

# Discord-side resource mutations.
_FORBIDDEN_DISCORD = {
    "create_text_channel",
    "create_category",
    "create_role",
    "edit",
    "delete",
    "set_permissions",
}

_FORBIDDEN = _FORBIDDEN_MUTATION | _FORBIDDEN_DISCORD


def _called_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for sub in ast.walk(tree):
        if isinstance(sub, ast.Call):
            func = sub.func
            if isinstance(func, ast.Attribute):
                names.add(func.attr)
            elif isinstance(func, ast.Name):
                names.add(func.id)
    return names


def test_advisor_review_module_makes_no_mutation_calls():
    tree = ast.parse(_MODULE.read_text(encoding="utf-8"))
    called = _called_names(tree)
    forbidden = called & _FORBIDDEN
    assert not forbidden, (
        "services.setup_advisor_review must be read-only but calls "
        f"forbidden mutation/DB/Discord primitive(s): {sorted(forbidden)}"
    )


def test_advisor_review_imports_no_mutation_pipeline():
    """Belt-and-braces: the module must not even import a mutation
    pipeline, so a future edit cannot quietly wire one in."""
    tree = ast.parse(_MODULE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
    forbidden_modules = {
        name
        for name in imported
        if "mutation" in name or name.endswith("resource_provisioning")
    }
    assert not forbidden_modules, (
        "services.setup_advisor_review imports mutation surface(s): "
        f"{sorted(forbidden_modules)}"
    )
