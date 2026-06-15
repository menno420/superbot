"""PR-04a invariant: setup preflight is strictly read-only.

The :func:`services.setup_operations.preflight_operations` adapters
must never write to the DB or invoke a mutation pipeline.  This test
walks the AST of ``setup_operations.py`` and asserts no preflight
adapter contains a mutation-pipeline call or a DB write helper.

If a future adapter needs to read from a heavy source, the contract
is to populate ``ChangePlanEntry.read_error`` (e.g.
``"preflight: skipped (heavy)"``) rather than fall back to a write.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SETUP_OPS = _REPO_ROOT / "disbot" / "services" / "setup_operations.py"

# Functions whose AST body must not contain any mutation calls.
_PREFLIGHT_FUNCS: frozenset[str] = frozenset(
    {
        "preflight_operations",
        "_preflight_bind",
        "_preflight_clear_binding",
        "_preflight_set_setting",
        "_preflight_set_cog_routing",
        "_preflight_set_role_threshold",
    },
)

# Forbidden attribute calls.  The preflight adapters can read these
# modules but must never invoke their mutation methods.
_FORBIDDEN_ATTR_NAMES: frozenset[str] = frozenset(
    {
        "set_binding",
        "clear_binding",
        "set_value",
        "set_setting",
        "set_policy",
        "create_rule",
        "set_enabled",
        "provision",
        "upsert_with_audit",
        "clear_with_audit",
        "set_cleanup_policy_for_scope",
        "create_channel",
        "create_role",
        "create_category",
        "set_one",  # utils.db.command_routing mutation
    },
)


def _find_preflight_function_bodies() -> dict[str, ast.AST]:
    """Return {func_name: AST body} for every preflight function."""
    tree = ast.parse(_SETUP_OPS.read_text(encoding="utf-8"))
    found: dict[str, ast.AST] = {}
    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in _PREFLIGHT_FUNCS
        ):
            found[node.name] = node
    return found


def test_every_preflight_function_present():
    found = _find_preflight_function_bodies()
    missing = _PREFLIGHT_FUNCS - found.keys()
    assert not missing, f"Expected preflight function(s) missing: {missing}"


def test_preflight_functions_call_no_mutation_method():
    """No preflight function may contain an attribute call whose name
    matches a known mutation method.  Adapters read from
    ``utils.db.bindings.get_one`` / ``db.get_setting`` /
    ``command_routing.is_cog_enabled`` — every other call is suspect."""
    violations: list[str] = []
    for name, node in _find_preflight_function_bodies().items():
        for sub in ast.walk(node):
            if not isinstance(sub, ast.Call):
                continue
            func = sub.func
            if isinstance(func, ast.Attribute) and func.attr in _FORBIDDEN_ATTR_NAMES:
                violations.append(f"{name}: calls .{func.attr}(...)")
    assert not violations, (
        "Preflight adapter(s) contain forbidden mutation call(s):\n  "
        + "\n  ".join(violations)
    )


def test_preflight_functions_do_not_open_db_transactions():
    """A preflight adapter using an explicit transaction would imply
    a write.  We forbid ``async with pool.acquire() as conn: async
    with conn.transaction():`` style usage by scanning for
    ``.transaction()`` calls inside preflight bodies."""
    violations: list[str] = []
    for name, node in _find_preflight_function_bodies().items():
        for sub in ast.walk(node):
            if not isinstance(sub, ast.Call):
                continue
            func = sub.func
            if isinstance(func, ast.Attribute) and func.attr == "transaction":
                violations.append(f"{name}: opens a transaction()")
    assert not violations, (
        "Preflight adapter(s) open a transaction — preflight is "
        "read-only:\n  " + "\n  ".join(violations)
    )


def test_preflight_module_does_not_import_mutation_pipelines_at_module_scope():
    """``setup_operations`` already forbids module-scope imports of
    pipeline modules (other invariant pins that).  PR-04a adapters
    must continue that discipline: any pipeline import stays
    function-local so the preflight read path cannot accidentally
    drag a mutation surface into scope."""
    tree = ast.parse(_SETUP_OPS.read_text(encoding="utf-8"))
    forbidden_modules = {
        "services.binding_mutation",
        "services.settings_mutation",
        "services.resource_provisioning",
        "services.automation_mutation",
    }
    violations: list[str] = []
    for node in tree.body:  # module-scope only
        if isinstance(node, ast.ImportFrom):
            if node.module in forbidden_modules:
                violations.append(f"module-scope from {node.module} import ...")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in forbidden_modules:
                    violations.append(f"module-scope import {alias.name}")
    if violations:
        pytest.fail(
            "setup_operations imports mutation pipeline at module scope:\n  "
            + "\n  ".join(violations),
        )
