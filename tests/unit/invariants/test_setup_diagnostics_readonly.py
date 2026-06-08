"""PR12 invariant: setup diagnostics is strictly read-only.

``services.setup_diagnostics`` *generates* typed :class:`SetupOperation`
repair batches but must never *apply* them: it owns detection,
classification, repairability, and op generation — Final Review (the
canonical dispatcher) owns mutation.  This AST check asserts the module

1. imports no concrete mutation pipeline (and not ``governance.writes``)
   at the top level, and
2. calls no mutation-pipeline method, ``apply_operations``, audited
   threshold write, or ``guild.create_*`` anywhere in the module.

Constructing ``SetupOperation(kind="clear_binding", ...)`` is fine — the
forbidden set targets *method calls*, not the operation-kind string.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MODULE = _REPO_ROOT / "disbot" / "services" / "setup_diagnostics.py"

_FORBIDDEN_TOP_LEVEL_IMPORTS: frozenset[str] = frozenset(
    {
        "services.binding_mutation",
        "services.settings_mutation",
        "services.resource_provisioning",
        "services.automation_mutation",
        "governance.writes",
    },
)

# Mutation method/function names the diagnostics layer must never invoke.
_FORBIDDEN_CALLS: frozenset[str] = frozenset(
    {
        "set_binding",
        "clear_binding",
        "set_value",
        "set_policy",
        "set_one",
        "create_rule",
        "set_enabled",
        "provision",
        "set_cleanup_policy_for_scope",
        "apply_cleanup_change",
        "set_time_threshold",
        "set_xp_threshold",
        "apply_operations",
        "execute",  # raw pool write
        "create_text_channel",
        "create_voice_channel",
        "create_category",
        "create_role",
        "create_thread",
    },
)


def _tree() -> ast.AST:
    return ast.parse(_MODULE.read_text(encoding="utf-8"))


def _top_level_import_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
    return names


def test_module_exists():
    assert _MODULE.exists(), f"setup_diagnostics.py not found at {_MODULE}"


def test_no_mutation_pipeline_imports_at_top_level():
    imports = _top_level_import_names(_tree())
    bad = _FORBIDDEN_TOP_LEVEL_IMPORTS & imports
    assert not bad, (
        "services/setup_diagnostics.py must not import mutation pipelines at the "
        "top level — it generates SetupOperation batches; Final Review dispatches "
        f"them.  Offending imports: {sorted(bad)}"
    )


def test_no_mutation_calls_anywhere():
    offenders: list[str] = []
    for node in ast.walk(_tree()):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr in _FORBIDDEN_CALLS:
            offenders.append(node.func.attr)
    assert not offenders, (
        "services/setup_diagnostics.py must be read-only — no mutation-pipeline "
        "call, threshold write, or guild.create_* is allowed. "
        f"Offending calls: {sorted(set(offenders))}"
    )


def test_does_not_import_setup_draft_anywhere():
    """Diagnostics generates ops but never stages them — that's the view's
    job (``views/setup/sections/diagnostics.py`` calls ``setup_draft.append``).
    Pin that the service imports ``setup_draft`` nowhere (top level or lazy).
    """
    offenders: list[str] = []
    for node in ast.walk(_tree()):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.endswith("setup_draft"):
                offenders.append(node.module)
            for alias in node.names:
                if alias.name == "setup_draft":
                    offenders.append(f"{node.module}.{alias.name}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.endswith("setup_draft"):
                    offenders.append(alias.name)
    assert not offenders, (
        "services/setup_diagnostics.py must not import setup_draft — staging the "
        f"generated repair ops is the section view's job.  Offending: {offenders}"
    )
