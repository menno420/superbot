"""Invariant tests for the setup operation dispatcher — PR 1.

Pins three structural constraints:

1. Setup views that act as recommendation-apply orchestrators must not
   import concrete mutation pipelines directly for their apply path.
   After the dispatcher migration, ``final_review.py`` routes all
   mutations through ``services.setup_operations``.

   Purpose-built pipeline UI panels (provisioning preview/confirm) are
   explicitly allowlisted: they are thin wrappers around one specific
   pipeline and are NOT generic orchestrators.  They migrate to the
   dispatcher in a dedicated future PR.

2. ``services.setup_operations`` must not import low-level
   ``utils.db.*`` mutation helpers at the top level.  All DB writes
   flow through the canonical pipeline APIs.

3. ``services.setup_operations`` must not call ``guild.create_*``
   methods directly.  That constraint is already enforced globally by
   ``test_no_silent_auto_create.py``; the third test here is a targeted
   pin that remains meaningful if the global allowlist is later widened.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"
_SETUP_VIEWS_DIR = _DISBOT / "views" / "setup"
_SETUP_OPS_PATH = _DISBOT / "services" / "setup_operations.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _iter_setup_view_files() -> list[Path]:
    return [
        p
        for p in _SETUP_VIEWS_DIR.rglob("*.py")
        if "__pycache__" not in p.parts and p.name != "__init__.py"
    ]


def _top_level_import_names(path: Path) -> set[str]:
    """Return the set of top-level module names imported by ``path``.

    Covers both ``import X`` and ``from X import Y`` where X is
    module-level (not inside a function or class).
    """
    tree = ast.parse(path.read_text())
    names: set[str] = set()
    for node in ast.iter_child_nodes(tree):  # only top-level nodes
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module.split(".")[0])
                names.add(node.module)
    return names


def _all_import_names(path: Path) -> set[str]:
    """Return every imported module name in ``path``, including in-function
    imports.

    The dispatcher migration removes top-level pipeline imports from
    setup-view modules, but a regression could sneak back in via a
    lazy in-function import (which still couples the view to the
    pipeline contract).  This helper feeds the "no nested forbidden
    pipeline imports" invariant below.
    """
    tree = ast.parse(path.read_text())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
            names.add(node.module)
    return names


def _has_attr_call(tree: ast.AST, attr_name: str) -> bool:
    """True if the AST contains any ``<expr>.<attr_name>(...)`` call."""
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == attr_name
        ):
            return True
    return False


_FORBIDDEN_PIPELINE_MODULES = {
    "services.binding_mutation",
    "services.settings_mutation",
    "services.resource_provisioning",
    "services.automation_mutation",
}

# Purpose-built pipeline UI panels are thin wrappers around one specific
# pipeline operation (preview / confirm a provisioning request).  They are
# NOT generic recommendation-apply orchestrators and are allowlisted here
# pending a future dedicated migration PR.
_PIPELINE_IMPORT_ALLOWLIST: set[Path] = {
    _SETUP_VIEWS_DIR / "provisioning" / "preview_panel.py",
    _SETUP_VIEWS_DIR / "provisioning" / "confirm_panel.py",
}

_FORBIDDEN_DB_PREFIXES = {
    "utils.db",
}

_FORBIDDEN_CREATE_METHODS = {
    "create_text_channel",
    "create_voice_channel",
    "create_category",
    "create_category_channel",
    "create_role",
    "create_thread",
}


# ---------------------------------------------------------------------------
# 1. Setup views must not import concrete mutation pipelines at top level
# ---------------------------------------------------------------------------


def test_setup_views_do_not_import_mutation_pipelines_at_top_level():
    """Setup view files outside the purpose-built-pipeline-UI allowlist must
    not import concrete mutation pipelines at module (top) level.

    After PR 1 the recommendation-apply path routes through
    services.setup_operations.  Pipelines may still appear inside function
    bodies (lazy imports) in any file; the constraint is top-level only.

    Files in ``_PIPELINE_IMPORT_ALLOWLIST`` are purpose-built pipeline UI
    panels (e.g. provisioning preview/confirm) and are exempted until a
    future migration PR migrates them to the dispatcher.
    """
    violations: list[str] = []
    for path in _iter_setup_view_files():
        if path in _PIPELINE_IMPORT_ALLOWLIST:
            continue
        imports = _top_level_import_names(path)
        bad = _FORBIDDEN_PIPELINE_MODULES & imports
        if bad:
            violations.append(
                f"{path.relative_to(_REPO_ROOT)}: imports {sorted(bad)}"
            )
    assert not violations, (
        "Setup view files must not import concrete mutation pipelines at the top "
        "level — route mutations through services.setup_operations instead.\n"
        "If this file is a purpose-built pipeline UI panel, add it to "
        "_PIPELINE_IMPORT_ALLOWLIST with a migration note.\n\n"
        + "\n".join(f"  {v}" for v in sorted(violations))
    )


def test_setup_views_invariant_path_exists():
    """The setup views directory must exist — catches a rename that would
    silently make this invariant vacuously true."""
    assert _SETUP_VIEWS_DIR.is_dir(), (
        f"disbot/views/setup/ not found at {_SETUP_VIEWS_DIR}; "
        "update the invariant path if the directory was renamed"
    )


def test_setup_views_do_not_import_mutation_pipelines_anywhere():
    """Stronger form of the top-level pipeline-import ban.

    After the template-picker dispatcher migration, no setup-view file
    outside the purpose-built-pipeline-UI allowlist should import a
    concrete mutation pipeline at *any* level (top-level or nested in a
    function body).  Lazy imports were used by the legacy
    ``apply_template_to_guild`` to dodge the top-level rule; this
    invariant closes that loophole.

    The allowlist still applies to the provisioning preview/confirm
    panels.
    """
    violations: list[str] = []
    for path in _iter_setup_view_files():
        if path in _PIPELINE_IMPORT_ALLOWLIST:
            continue
        imports = _all_import_names(path)
        bad = _FORBIDDEN_PIPELINE_MODULES & imports
        if bad:
            violations.append(f"{path.relative_to(_REPO_ROOT)}: imports {sorted(bad)}")
    assert not violations, (
        "Setup view files must not import concrete mutation pipelines at any "
        "level (including in-function lazy imports) — route mutations through "
        "services.setup_operations instead.\n"
        "If this file is a purpose-built pipeline UI panel, add it to "
        "_PIPELINE_IMPORT_ALLOWLIST with a migration note.\n\n"
        + "\n".join(f"  {v}" for v in sorted(violations))
    )


# ---------------------------------------------------------------------------
# 2. setup_operations.py must not import utils.db.* at top level
# ---------------------------------------------------------------------------


def test_setup_operations_does_not_import_db_utils_at_top_level():
    """services/setup_operations.py must not import utils.db.* helpers at
    module level.  All DB writes route through the canonical pipeline APIs.
    """
    assert _SETUP_OPS_PATH.exists(), (
        f"services/setup_operations.py not found at {_SETUP_OPS_PATH}"
    )
    imports = _top_level_import_names(_SETUP_OPS_PATH)
    bad = {m for m in imports if any(m.startswith(p) for p in _FORBIDDEN_DB_PREFIXES)}
    assert not bad, (
        "services/setup_operations.py must not import utils.db.* at the top level — "
        "all DB writes must flow through the canonical pipeline APIs (e.g. "
        "BindingMutationPipeline).  Offending imports:\n  "
        + "\n  ".join(sorted(bad))
    )


# ---------------------------------------------------------------------------
# 3. setup_operations.py must not call guild.create_* directly
# ---------------------------------------------------------------------------


def test_setup_operations_does_not_call_guild_create_directly():
    """services/setup_operations.py must not call any guild.create_*
    method.  Resource creation must route through
    ResourceProvisioningPipeline which in turn calls guild_resources.ensure_*.
    """
    assert _SETUP_OPS_PATH.exists()
    tree = ast.parse(_SETUP_OPS_PATH.read_text())
    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr in _FORBIDDEN_CREATE_METHODS:
            offenders.append(node.func.attr)
    assert not offenders, (
        "services/setup_operations.py must not call guild.create_* directly — "
        "route resource creation through ResourceProvisioningPipeline.provision(). "
        "Offending calls:\n  " + "\n  ".join(offenders)
    )
