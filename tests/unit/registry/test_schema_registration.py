"""Invariant: every subsystem that declares a schema must register it (S5).

A subsystem with ``cogs/<name>/schemas.py:register_schemas`` is declared
but only becomes reachable from the Settings hub when its cog calls
``register_schemas()`` from :meth:`cog_load`. A previous audit
incorrectly claimed moderation/xp schemas were declared but not
registered — this test pins the actual state so a future PR can't
silently regress it.

The test is AST-based so it works without loading the cog (which
would require database / token setup).
"""

from __future__ import annotations

import ast
from pathlib import Path

_DISBOT = Path(__file__).parents[3] / "disbot"
_COGS_DIR = _DISBOT / "cogs"


def _cogs_declaring_schemas() -> dict[str, Path]:
    """Return ``{subsystem -> schemas.py path}`` for every subdirectory
    cog package whose ``schemas.py`` defines ``register_schemas``.
    """
    declarers: dict[str, Path] = {}
    for schemas_py in _COGS_DIR.glob("*/schemas.py"):
        try:
            tree = ast.parse(schemas_py.read_text(), filename=str(schemas_py))
        except SyntaxError:
            continue
        has_register = any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "register_schemas"
            for node in ast.walk(tree)
        )
        if has_register:
            declarers[schemas_py.parent.name] = schemas_py
    return declarers


def _cog_file_for_subsystem(subsystem: str) -> Path | None:
    """Find the ``cogs/<subsystem>_cog.py`` file that owns the subsystem."""
    candidate = _COGS_DIR / f"{subsystem}_cog.py"
    if candidate.exists():
        return candidate
    return None


def _cog_load_calls_register_schemas(cog_path: Path) -> bool:
    """Return True if any ``cog_load`` method in the cog file calls
    ``register_schemas()``.
    """
    tree = ast.parse(cog_path.read_text(), filename=str(cog_path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef):
            continue
        if node.name != "cog_load":
            continue
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            func = child.func
            # Match both `register_schemas()` and `module.register_schemas()`.
            if isinstance(func, ast.Name) and func.id == "register_schemas":
                return True
            if isinstance(func, ast.Attribute) and func.attr == "register_schemas":
                return True
    return False


def test_every_schema_declaring_cog_registers_in_cog_load():
    """Invariant: declaring ``cogs/<name>/schemas.py:register_schemas``
    without calling it from ``<name>_cog.py:cog_load`` leaves the
    schema orphaned — settings hub can't discover it, audit pipelines
    can't enforce capability requirements.

    Pinning this prevents a regression where a developer adds a new
    schema file but forgets the cog_load wiring.
    """
    declarers = _cogs_declaring_schemas()
    assert declarers, "expected at least one cog to declare schemas"

    orphaned: list[str] = []
    missing_cog_file: list[str] = []
    for subsystem in declarers:
        cog_path = _cog_file_for_subsystem(subsystem)
        if cog_path is None:
            missing_cog_file.append(subsystem)
            continue
        if not _cog_load_calls_register_schemas(cog_path):
            orphaned.append(f"{subsystem} → {cog_path.name}")

    assert not missing_cog_file, (
        "schemas.py declares register_schemas() but the owning "
        "cogs/<name>_cog.py is missing:\n  " + "\n  ".join(missing_cog_file)
    )
    assert not orphaned, (
        "schemas.py declares register_schemas() but cog_load() never "
        "calls it — settings hub won't discover these schemas:\n  "
        + "\n  ".join(orphaned)
    )


def test_known_subsystems_with_schemas_are_present():
    """Pin the set of subsystems that have schemas today, so a future
    PR that accidentally removes one fails CI loudly.
    """
    declarers = set(_cogs_declaring_schemas())
    expected = {"economy", "logging", "moderation", "xp"}
    missing = expected - declarers
    assert not missing, (
        f"expected schemas for {expected}; missing: {missing}. "
        "If a schema was deliberately removed, update this test."
    )
