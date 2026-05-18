"""S5 invariant — Settings Manager cog + views are strictly read-only.

The S5 directive is explicit: the cog and its views must not edit,
reset, mutate, create, or otherwise change platform state.  S6
introduces the first write surface (scalar edit/reset flows) and
will explicitly add the mutation imports the AST scan below
forbids.

This test fails CI if any file under:

  * ``disbot/cogs/settings*``
  * ``disbot/views/settings/**``

imports any mutation pipeline or directly invokes a mutation
method.  When S6 lands, this invariant tightens to allow the
expected mutation imports inside an allowlist of edit-flow files.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"


# Modules and functions whose presence inside Settings Manager UI
# would imply a write path.  These are not exhaustive; they cover
# the four mutation pipelines + a few common write-shape callables.
_FORBIDDEN_IMPORT_PREFIXES: frozenset[str] = frozenset(
    {
        "services.settings_mutation",
        "services.binding_mutation",
        "services.resource_provisioning",  # creator/binder of Discord resources
        "services.participation_mutation",
        "services.rollout_mutation",
        "governance.writes",
    },
)

# Discord-API resource-create methods.  Any reference inside the
# settings UI surface would be a violation regardless of how they
# are invoked.
_FORBIDDEN_DIRECT_METHODS: frozenset[str] = frozenset(
    {
        "create_text_channel",
        "create_voice_channel",
        "create_category",
        "create_category_channel",
        "create_role",
        "create_thread",
    },
)

# Mutation methods on the four canonical pipelines.  Catches the
# case where someone imports the pipeline by another name and then
# calls these via attribute access — defense-in-depth above the
# import-level scan.
_FORBIDDEN_METHOD_CALLS: frozenset[str] = frozenset(
    {
        "set_value",  # SettingsMutationPipeline.set_value
        "set_binding",  # BindingMutationPipeline.set_binding
        "clear_binding",  # BindingMutationPipeline.clear_binding
        "set_visibility",  # GovernanceMutationPipeline.set_visibility
        "set_cleanup_policy",
        "set_cleanup_policy_for_scope",
        "provision",  # ResourceProvisioningPipeline.provision
    },
)


def _settings_ui_paths() -> list[Path]:
    """Return every production .py file inside the Settings Manager UI surface."""
    out: list[Path] = []
    for candidate in [
        _DISBOT / "cogs" / "settings_cog.py",
        *(_DISBOT / "cogs" / "settings").rglob("*.py"),
        *(_DISBOT / "views" / "settings").rglob("*.py"),
    ]:
        if "__pycache__" in candidate.parts:
            continue
        if candidate.exists():
            out.append(candidate)
    return out


def _module_imports_offenders(tree: ast.AST) -> list[str]:
    offenders: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for needle in _FORBIDDEN_IMPORT_PREFIXES:
                if node.module == needle or node.module.startswith(needle + "."):
                    offenders.append(
                        f"from {node.module} import "
                        f"{', '.join(a.name for a in node.names)}",
                    )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                for needle in _FORBIDDEN_IMPORT_PREFIXES:
                    if alias.name == needle or alias.name.startswith(needle + "."):
                        offenders.append(f"import {alias.name}")
    return offenders


def _attribute_call_offenders(tree: ast.AST) -> list[str]:
    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        attr = node.func.attr
        if attr in _FORBIDDEN_DIRECT_METHODS or attr in _FORBIDDEN_METHOD_CALLS:
            offenders.append(attr)
    return offenders


def test_settings_ui_has_no_mutation_imports():
    """No file under the Settings Manager UI surface may import a
    mutation pipeline.
    """
    paths = _settings_ui_paths()
    assert paths, "settings UI paths empty — sanity check failed"
    violations: list[tuple[str, list[str]]] = []
    for path in paths:
        tree = ast.parse(path.read_text(), filename=str(path))
        offenders = _module_imports_offenders(tree)
        if offenders:
            violations.append((str(path.relative_to(_REPO_ROOT)), offenders))
    assert not violations, (
        "S5 invariant violation: Settings Manager UI surface imports a "
        "mutation pipeline.  S5 is strictly read-only; S6 introduces the "
        "first edit/reset flow.\n\n"
        + "\n".join(f"  {p}: {imps}" for p, imps in violations)
    )


def test_settings_ui_does_not_call_known_mutation_methods():
    """No file under the Settings Manager UI surface may *call* any
    of the canonical mutation methods (or any Discord-API create
    method).  Defense-in-depth above the import scan.
    """
    paths = _settings_ui_paths()
    violations: list[tuple[str, list[str]]] = []
    for path in paths:
        tree = ast.parse(path.read_text(), filename=str(path))
        offenders = _attribute_call_offenders(tree)
        if offenders:
            violations.append((str(path.relative_to(_REPO_ROOT)), offenders))
    assert not violations, (
        "S5 invariant violation: Settings Manager UI calls a mutation "
        "or resource-creation method.  S5 is strictly read-only.\n\n"
        + "\n".join(f"  {p}: {calls}" for p, calls in violations)
    )


def test_settings_ui_paths_contain_expected_files():
    """The scanner must actually find the S5 files we ship.

    Otherwise a renamed-file refactor could weaken the invariant
    silently.
    """
    paths = {p.relative_to(_REPO_ROOT) for p in _settings_ui_paths()}
    expected_relpaths = {
        Path("disbot/cogs/settings_cog.py"),
        Path("disbot/cogs/settings/__init__.py"),
        Path("disbot/views/settings/__init__.py"),
        Path("disbot/views/settings/hub.py"),
        Path("disbot/views/settings/subsystem_view.py"),
        Path("disbot/views/settings/needs_setup.py"),
        Path("disbot/views/settings/invalid_settings.py"),
        Path("disbot/views/settings/missing_bindings.py"),
        Path("disbot/views/settings/audit_view.py"),
    }
    missing = expected_relpaths - paths
    assert (
        not missing
    ), "S5 invariant scanner did not pick up these expected files:\n" + "\n".join(
        f"  {p}" for p in sorted(missing)
    )
