"""Phase 2 PR-7 invariant — no direct branching on ``bindings.primary``.

The Phase 2 plan forbids per-cog (or per-service / per-governance)
branching on ``is_enabled("bindings.primary", ...)``.  Only
:mod:`core.runtime.config_arbitration` may consult that flag; all
other consumers route reads through the typed per-subsystem
accessors (``get_xp_announce_channel`` etc.) which encapsulate the
flag check.

Why this matters:
* The canary flip of ``bindings.primary`` is a single change in
  the arbitration module; scattered branches would multiply the
  rollback surface.
* Provenance (``ConfigReadResult.source``, ``binding_status``,
  ``flag_state``, ``diagnostics``) is only captured by the central
  helper — per-cog branches would lose it.

This test parses every ``disbot/**/*.py`` file via AST and fails if
any node references the string literal ``"bindings.primary"`` outside
the allowlist below.

Allowlist:
* ``disbot/core/runtime/config_arbitration.py`` — the only legitimate
  consumer.
* ``disbot/core/runtime/feature_flags.py`` — declares the flag.
* ``disbot/services/binding_backfill.py`` — uses the literal as the
  migration name and in checkpoint payloads, not as a flag check.
* ``disbot/services/rollout_mutation.py`` — error messages reference
  ``"bindings.primary"`` as an example.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCAN_ROOT = _REPO_ROOT / "disbot"
_FLAG_LITERAL = "bindings.primary"

# Files allowed to reference the literal.  Add to this list with care
# — every entry weakens the invariant.
_ALLOWLIST = {
    _SCAN_ROOT / "core" / "runtime" / "config_arbitration.py",
    _SCAN_ROOT / "core" / "runtime" / "feature_flags.py",
    _SCAN_ROOT / "services" / "binding_backfill.py",
    _SCAN_ROOT / "services" / "rollout_mutation.py",
}


def _iter_python_files() -> list[Path]:
    return [p for p in _SCAN_ROOT.rglob("*.py") if "__pycache__" not in p.parts]


def _file_references_literal(path: Path) -> bool:
    """True if the AST contains a ``str`` constant equal to ``bindings.primary``."""
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError:
        # Not a valid python module — skip rather than crash the test
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and node.value == _FLAG_LITERAL:
            return True
    return False


def test_no_direct_bindings_primary_outside_allowlist():
    """Every reference to ``"bindings.primary"`` lives in the allowlist."""
    violations: list[str] = []
    for path in _iter_python_files():
        if path in _ALLOWLIST:
            continue
        if _file_references_literal(path):
            violations.append(str(path.relative_to(_REPO_ROOT)))
    assert not violations, (
        "These files reference the literal 'bindings.primary' but are "
        "not in the allowlist — route reads through "
        "core.runtime.config_arbitration's per-subsystem accessors "
        "(get_xp_announce_channel, get_economy_log_channel, "
        "get_trusted_tier_role) instead.\n\n"
        + "\n".join(f"  {v}" for v in sorted(violations))
    )


def test_allowlist_entries_exist():
    """Every file in the allowlist must still exist on disk.

    Otherwise a renamed file would silently relax the invariant.
    """
    missing = [str(p.relative_to(_REPO_ROOT)) for p in _ALLOWLIST if not p.exists()]
    assert (
        not missing
    ), "Allowlist references files that no longer exist:\n" + "\n".join(
        f"  {p}" for p in missing
    )


def test_arbitration_module_actually_references_literal():
    """If the allowlist target itself stops referencing the flag, the
    invariant is meaningless.  Pin that config_arbitration still
    consumes the literal.
    """
    arbitration = _SCAN_ROOT / "core" / "runtime" / "config_arbitration.py"
    assert _file_references_literal(
        arbitration,
    ), "core/runtime/config_arbitration.py must reference 'bindings.primary'"
