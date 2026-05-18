"""S5/S6 invariant — Settings Manager UI mutation surface is allowlisted.

S5 (PR #100) shipped the Settings Manager hub + subsystem
drill-down + four diagnostic sub-panels in strictly read-only
form.  S6 (this PR) extends the subsystem view with scalar
edit/reset flows that route writes through
:class:`services.settings_mutation.SettingsMutationPipeline`.

This test now scans every file under:

  * ``disbot/cogs/settings*``
  * ``disbot/views/settings/**``

and fails CI if any file imports a mutation pipeline OR calls a
known mutation/create method **unless that file is on the S6
allowlist** (:data:`_ALLOWED_EDIT_FILES`).  The allowlist is the
five edit-flow widget modules plus the reset module — every other
file in the Settings UI surface stays read-only.

When S7 lands and adds binding-edit flows, this allowlist
expands; access-policy edits arrive in S9 and similarly extend
the allowlist.  Every new allowlist entry MUST justify why the
bypass is correct (typically: "the file IS the mutation surface
for a typed scalar/binding/policy").
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


# Files allowed to import a mutation pipeline / call a mutation
# method.  S6 lifted the invariant to permit the five edit-flow
# widgets + the reset module; nothing else in the Settings UI
# surface may write.  Adding entries here weakens the invariant —
# pair each new entry with a comment naming the milestone that
# introduced the bypass and the mutation surface it owns.
_ALLOWED_EDIT_FILES: frozenset[Path] = frozenset(
    {
        # S6 — scalar edit / reset flows.
        _DISBOT / "views" / "settings" / "edit_boolean.py",
        _DISBOT / "views" / "settings" / "edit_number.py",
        _DISBOT / "views" / "settings" / "edit_text.py",
        _DISBOT / "views" / "settings" / "edit_enum.py",
        _DISBOT / "views" / "settings" / "reset_button.py",
    },
)


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


def test_settings_ui_has_no_mutation_imports_outside_allowlist():
    """No file under the Settings Manager UI surface may import a
    mutation pipeline UNLESS it is on :data:`_ALLOWED_EDIT_FILES`.
    """
    paths = _settings_ui_paths()
    assert paths, "settings UI paths empty — sanity check failed"
    violations: list[tuple[str, list[str]]] = []
    for path in paths:
        if path in _ALLOWED_EDIT_FILES:
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        offenders = _module_imports_offenders(tree)
        if offenders:
            violations.append((str(path.relative_to(_REPO_ROOT)), offenders))
    assert not violations, (
        "S5/S6 invariant violation: Settings Manager UI file imports a "
        "mutation pipeline but is not on the edit-flow allowlist.  Either "
        "remove the import or extend `_ALLOWED_EDIT_FILES` with a "
        "justification.\n\n" + "\n".join(f"  {p}: {imps}" for p, imps in violations)
    )


def test_settings_ui_does_not_call_known_mutation_methods_outside_allowlist():
    """No file under the Settings Manager UI surface may *call* any
    canonical mutation method UNLESS it is on the edit-flow
    allowlist.  Defense-in-depth above the import scan.
    """
    paths = _settings_ui_paths()
    violations: list[tuple[str, list[str]]] = []
    for path in paths:
        if path in _ALLOWED_EDIT_FILES:
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        offenders = _attribute_call_offenders(tree)
        if offenders:
            violations.append((str(path.relative_to(_REPO_ROOT)), offenders))
    assert not violations, (
        "S5/S6 invariant violation: Settings Manager UI file calls a "
        "mutation or resource-creation method but is not on the edit-flow "
        "allowlist.\n\n" + "\n".join(f"  {p}: {calls}" for p, calls in violations)
    )


def test_allowlist_entries_exist():
    """Every allowlist entry must still exist on disk."""
    missing = [
        str(p.relative_to(_REPO_ROOT)) for p in _ALLOWED_EDIT_FILES if not p.exists()
    ]
    assert not missing, "S6 allowlist references missing files:\n" + "\n".join(
        f"  {p}" for p in missing
    )


def test_allowlist_only_contains_edit_flow_files():
    """Sanity: the allowlist must only contain ``views/settings/edit_*`` and
    ``views/settings/reset_*`` files.  Catches a future drive-by edit that
    allowlists, say, the hub or audit view by mistake."""
    for path in _ALLOWED_EDIT_FILES:
        name = path.name
        assert name.startswith("edit_") or name.startswith(
            "reset_"
        ), f"unexpected allowlist entry: {path.relative_to(_REPO_ROOT)}"


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
        # S6 edit flow:
        Path("disbot/views/settings/edit_boolean.py"),
        Path("disbot/views/settings/edit_number.py"),
        Path("disbot/views/settings/edit_text.py"),
        Path("disbot/views/settings/edit_enum.py"),
        Path("disbot/views/settings/reset_button.py"),
    }
    missing = expected_relpaths - paths
    assert (
        not missing
    ), "S5 invariant scanner did not pick up these expected files:\n" + "\n".join(
        f"  {p}" for p in sorted(missing)
    )
