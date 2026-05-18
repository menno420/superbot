"""F-2 invariant — every settings key lives in a per-subsystem submodule.

Static AST scan that fails the build if a constant is added directly to
``disbot/utils/settings_keys/__init__.py``.  Constants must live in the
appropriate subsystem submodule (``xp.py``, ``economy.py``, …); the
``__init__`` only re-exports them.

Why the discipline matters:

  * ``settings_keys/__init__.py`` is the back-compat surface for the
    legacy flat ``utils.settings_keys`` import path.  If it grows
    constants of its own, ownership of those keys is ambiguous.
  * The wizard / configuration runtime work introduced in Phase 1+ of
    the platform roadmap iterates over per-subsystem schemas; a key
    defined only in the package root has no schema owner.
  * Adding a new subsystem becomes a *mechanical* operation: create
    ``settings_keys/<subsystem>.py``, add the import in ``__init__``.

The flat module ``utils/settings_keys.py`` was split into a package in
Phase 0; this invariant prevents the package from regressing into a
single-file shape.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_PACKAGE_ROOT = _REPO_ROOT / "disbot" / "utils" / "settings_keys"
_INIT_PATH = _PACKAGE_ROOT / "__init__.py"


def _module_level_assigned_names(path: Path) -> list[str]:
    """Return names of module-level constant assignments in *path*.

    Only returns names that look like constants (UPPER_SNAKE_CASE) so the
    invariant ignores private helpers, type aliases, and the like.
    """
    tree = ast.parse(path.read_text(), filename=str(path))
    found: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    found.append(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id.isupper():
                found.append(node.target.id)
    return found


def test_settings_keys_package_exists():
    """The package layout is the canonical shape; regressing to a flat
    file would defeat the invariant entirely.
    """
    assert _PACKAGE_ROOT.is_dir(), (
        f"settings_keys must be a package directory at {_PACKAGE_ROOT}; "
        "the flat utils/settings_keys.py shape was retired in Phase 0."
    )
    assert _INIT_PATH.is_file(), (
        f"settings_keys package must expose {_INIT_PATH.name} as the "
        "back-compat re-export surface."
    )


def test_init_defines_no_module_level_constants():
    """``__init__.py`` is a re-export surface; constants belong in submodules."""
    assigned = _module_level_assigned_names(_INIT_PATH)
    assert not assigned, (
        "F-2 invariant violation: settings_keys/__init__.py defines "
        f"constants directly: {assigned}.  Move them into the appropriate "
        "subsystem submodule (xp.py, economy.py, moderation.py, role.py, "
        "games.py, governance.py, …) and re-export from __init__.py."
    )


def test_init_imports_from_subsystem_submodules_only():
    """Every import in ``__init__.py`` must come from a submodule of the
    package itself.  This stops accidental re-exports from unrelated
    modules sneaking into the canonical key namespace.
    """
    tree = ast.parse(_INIT_PATH.read_text(), filename=str(_INIT_PATH))
    bad: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        # Allow `from . import X` and `from utils.settings_keys.<sub> import X`.
        mod = node.module or ""
        if mod.startswith("utils.settings_keys."):
            continue
        if mod == "utils.settings_keys":
            continue
        if node.level >= 1:
            # Relative import inside the package; fine.
            continue
        bad.append(f"from {mod} import {', '.join(a.name for a in node.names)}")
    assert not bad, (
        "F-2 invariant violation: settings_keys/__init__.py imports from "
        "modules outside the package.  Re-exports must originate in "
        f"settings_keys/<subsystem>.py.\n  Offenders: {bad}"
    )


def _subsystem_submodules() -> list[Path]:
    return sorted(p for p in _PACKAGE_ROOT.glob("*.py") if p.name != "__init__.py")


@pytest.mark.parametrize(
    "submodule",
    sorted(p.relative_to(_REPO_ROOT) for p in _subsystem_submodules()),
)
def test_submodule_defines_at_least_one_constant(submodule):
    """Empty submodules clutter the namespace; require each submodule to
    own at least one constant so the per-subsystem grouping is meaningful.
    """
    path = _REPO_ROOT / submodule
    assigned = _module_level_assigned_names(path)
    assert assigned, (
        f"F-2 invariant: {submodule} defines no UPPER_CASE constants — "
        "delete the file or add the keys it owns."
    )


def test_init_re_exports_every_submodule_constant():
    """If a constant exists in a submodule but is not re-exported from
    ``__init__.py``, the legacy ``from utils.settings_keys import NAME``
    path silently breaks.
    """
    submodule_constants: dict[str, set[str]] = {}
    for sub in _subsystem_submodules():
        submodule_constants[sub.stem] = set(_module_level_assigned_names(sub))

    init_tree = ast.parse(_INIT_PATH.read_text(), filename=str(_INIT_PATH))
    re_exported: set[str] = set()
    for node in ast.walk(init_tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
            "utils.settings_keys.",
        ):
            re_exported.update(alias.name for alias in node.names)

    missing: list[str] = []
    for sub, consts in submodule_constants.items():
        for name in consts:
            if name not in re_exported:
                missing.append(f"{sub}.{name}")
    assert not missing, (
        "F-2 invariant violation: constants defined in submodules but "
        "not re-exported from settings_keys/__init__.py:\n  " + "\n  ".join(missing)
    )
