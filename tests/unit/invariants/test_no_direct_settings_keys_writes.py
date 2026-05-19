"""S4 invariant — every ``db.set_setting`` caller is on the allowlist.

The Settings Manager roadmap (S4) introduces
:class:`services.settings_mutation.SettingsMutationPipeline` as the
canonical write path for scalar ``SettingSpec`` values backed by the
legacy ``guild_settings`` KV.  New code MUST route through the
pipeline; existing call sites are allowlisted and will migrate
per-subsystem in S10.

Why bare ``db.set_setting`` callers are dangerous in the new world:

  * The pipeline performs typed coercion, validation, audit, cache
    invalidation, and event emission.  Bypassing it loses every
    one of those guarantees.
  * Audit history is incomplete if some writers skip the pipeline.

This test parses every ``disbot/**/*.py`` file via AST and fails if
any node references ``set_setting`` outside the allowlist.  The
allowlist documents the migration target — each entry is a candidate
for routing through the pipeline in a later milestone (typically the
per-subsystem S10 work).

Allowlist structure:

  * The DB primitive itself (``utils/db/settings.py``) and its
    re-export module (``utils/db/__init__.py``) — they DEFINE the
    function.
  * The new pipeline service and its DB layer — they implement the
    canonical write path.
  * Pre-existing callers — frozen here so a new caller cannot slip
    in without a discussion.  Each entry is paired with a comment
    naming the future migration milestone.

A new caller wanting to bypass the pipeline must either:

  * Migrate to ``SettingsMutationPipeline.set_value(...)``; or
  * Add itself to the allowlist with a comment explaining why
    bypassing the pipeline is correct for this caller.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

# Files ALLOWED to reference ``set_setting`` (call or import).
# Adding to this list weakens the invariant; do not extend casually.
_ALLOWED_PATHS = {
    # The primitive itself.
    _DISBOT / "utils" / "db" / "settings.py",
    # Re-export module (re-exports ``set_setting`` from ``utils.db.settings``).
    _DISBOT / "utils" / "db" / "__init__.py",
    # Pre-existing callers — migrate to SettingsMutationPipeline in S10.
    # Each entry below corresponds to a per-subsystem S10 sub-PR
    # ("settings/<subsystem>") that will route the call through the
    # pipeline and remove the entry.
    _DISBOT / "cogs" / "blackjack_cog.py",        # ACTIVE_TOURNAMENT writes
    # ``cogs/economy_cog.py`` migrated to SettingsMutationPipeline in PR #6
    # — removed from the allowlist (the AST scan now enforces it).
    _DISBOT / "cogs" / "rps_tournament_cog.py",   # ACTIVE_TOURNAMENT writes
    _DISBOT / "cogs" / "rps_tournament" / "_helpers.py",  # ACTIVE_TOURNAMENT
    _DISBOT / "governance" / "writes.py",         # internal governance writes
    _DISBOT / "views" / "blackjack" / "tournament_views.py",
    # ``views/xp/modals.py`` migrated to SettingsMutationPipeline in PR #5
    # — removed from the allowlist (the AST scan now enforces it).
    # Documentation reference (string literal in a module docstring,
    # not a call) — kept on the allowlist so the docstring is not
    # forced to rephrase.
    _DISBOT / "utils" / "settings_keys" / "__init__.py",
}

_FORBIDDEN_NAME = "set_setting"


def _iter_production_py_files() -> list[Path]:
    return [p for p in _DISBOT.rglob("*.py") if "__pycache__" not in p.parts]


def _attribute_calls(tree: ast.AST) -> list[str]:
    """Return ``"<receiver>.set_setting"`` for any ``<receiver>.set_setting(...)``
    call where ``<receiver>`` ends in ``db`` or ``settings``.
    """
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != _FORBIDDEN_NAME:
            continue
        rcv = node.func.value
        parts: list[str] = []
        while isinstance(rcv, ast.Attribute):
            parts.append(rcv.attr)
            rcv = rcv.value
        if isinstance(rcv, ast.Name):
            parts.append(rcv.id)
        receiver = ".".join(reversed(parts))
        # Receiver's final segment must be "db" or "settings" to count
        # (filters out unrelated attributes named ``set_setting`` on
        # objects that are not the legacy-KV primitive).
        last = receiver.split(".")[-1]
        if last in {"db", "settings"}:
            found.append(f"{receiver}.{node.func.attr}")
    return found


def _direct_imports(tree: ast.AST) -> list[str]:
    """Return forbidden names directly imported via ``from ... import set_setting``."""
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.module is None:
            continue
        # Match utils.db, utils.db.settings, and any submodule path
        # ending in those.
        if not (
            node.module == "utils.db"
            or node.module == "utils.db.settings"
            or node.module.endswith(".utils.db")
            or node.module.endswith(".utils.db.settings")
        ):
            continue
        for alias in node.names:
            if alias.name == _FORBIDDEN_NAME:
                found.append(f"from {node.module} import {alias.name}")
    return found


def test_no_bare_set_setting_outside_allowlist():
    """No production file outside the allowlist may call
    ``db.set_setting`` directly or import it from the primitive
    module.
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
        "S4 invariant violation: bare db.set_setting access outside "
        "the SettingsMutationPipeline allowlist.\n"
        "Route new writes through "
        "services.settings_mutation.SettingsMutationPipeline.set_value(...) "
        "or extend the allowlist explicitly with a justification.\n\n"
        + "\n".join(f"  {p}: {calls}" for p, calls in violations)
    )


def test_allowlist_entries_exist():
    """Every allowlisted file must still exist on disk.

    A renamed file would silently relax the invariant.
    """
    missing = [
        str(p.relative_to(_REPO_ROOT)) for p in _ALLOWED_PATHS if not p.exists()
    ]
    assert not missing, (
        "S4 allowlist references files that no longer exist:\n"
        + "\n".join(f"  {p}" for p in missing)
    )


def test_pipeline_does_not_call_set_setting_directly():
    """The pipeline service must NOT call ``db.set_setting`` — it
    writes via ``utils.db.settings_audit.set_value_with_audit`` so
    the legacy-KV write and the audit insert land atomically.
    """
    pipeline_path = _DISBOT / "services" / "settings_mutation.py"
    text = pipeline_path.read_text()
    assert (
        ".set_setting(" not in text
    ), "services.settings_mutation must not call db.set_setting directly"
