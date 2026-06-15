"""F-1 invariant — every guild_config.{get,get_many} call goes through a typed accessor.

Static AST scan that fails the build if any production file outside the
allowlist either:

  * calls ``guild_config.get(...)`` / ``guild_config.get_many(...)``
    via attribute access on the imported module, or
  * imports those names directly via ``from ... import get, get_many``.

The discipline:

    cogs / views / services
        ↓
    utils.guild_config_accessors            ← canonical key strings live here
        ↓
    core.runtime.guild_config               ← the primitive

Why bare-string callers are dangerous:

  * A typo in the key produces a silent cross-consumer hash collision —
    two unrelated consumers reading the same key would share the cached
    value of whichever loaded first.
  * The key string becomes part of the implicit cache schema with no
    discoverable owner; ``!platform caches`` cannot map metrics back to
    a feature.

The typed-accessor module owns the canonical key string for each
consumer; cogs import the accessor and never name the key directly.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

# Files ALLOWED to call guild_config.{get,get_many} directly.
_ALLOWED_PATHS = {
    _DISBOT / "core" / "runtime" / "guild_config.py",  # the primitive itself
    _DISBOT / "utils" / "guild_config_accessors.py",  # canonical typed wrappers
}

_FORBIDDEN_NAMES = {"get", "get_many"}


def _iter_production_py_files() -> list[Path]:
    return [p for p in _DISBOT.rglob("*.py") if "__pycache__" not in p.parts]


def _attribute_calls(tree: ast.AST) -> list[str]:
    """Return ``"<receiver>.<name>"`` for any ``<receiver>.<name>(...)`` call
    where ``<receiver>`` is dotted-ending in ``guild_config`` and ``<name>``
    is a forbidden primitive name.
    """
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in _FORBIDDEN_NAMES:
            continue
        rcv = node.func.value
        parts: list[str] = []
        while isinstance(rcv, ast.Attribute):
            parts.append(rcv.attr)
            rcv = rcv.value
        if isinstance(rcv, ast.Name):
            parts.append(rcv.id)
        receiver = ".".join(reversed(parts))
        # Receiver's final segment must be "guild_config" to count.
        if receiver.split(".")[-1] == "guild_config":
            found.append(f"{receiver}.{node.func.attr}")
    return found


def _direct_imports(tree: ast.AST) -> list[str]:
    """Return forbidden names directly imported via ``from ...guild_config import ...``."""
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.module is None:
            continue
        if not node.module.endswith("guild_config"):
            continue
        for alias in node.names:
            if alias.name in _FORBIDDEN_NAMES:
                found.append(f"from {node.module} import {alias.name}")
    return found


def test_no_bare_guild_config_access_outside_accessors():
    """No production file outside the allowlist may call guild_config.get/get_many
    directly or import those names from the primitive module.
    """
    violations: list[tuple[str, list[str]]] = []
    for path in _iter_production_py_files():
        if path in _ALLOWED_PATHS:
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        offenders = _attribute_calls(tree) + _direct_imports(tree)
        if offenders:
            violations.append((str(path.relative_to(_REPO_ROOT)), offenders))
    assert not violations, (
        "F-1 invariant violation: bare guild_config.{get,get_many} access "
        "outside utils.guild_config_accessors.\n"
        "Wrap each consumer in a typed accessor in that module.\n\n"
        + "\n".join(f"  {p}: {calls}" for p, calls in violations)
    )


@pytest.mark.parametrize(
    "allowed_path",
    sorted(p.relative_to(_REPO_ROOT) for p in _ALLOWED_PATHS),
)
def test_allow_list_files_actually_exist(allowed_path):
    """If the allowlist drifts from the filesystem the test weakens silently."""
    p = _REPO_ROOT / allowed_path
    assert p.exists(), f"F-1 allowlist references missing file: {allowed_path}"
