"""Moderation-convergence invariant — manual moderation actions route
through ``services.moderation_service``.

Static AST scan of the moderation adapter surfaces (``cogs/moderation*``
and ``views/moderation*``).  After the server-management PR1 convergence
these adapters must not perform moderation mutations directly: every
warn / timeout / kick / ban / unban / clear-warnings goes through
``services.moderation_service`` — the single audited writer that appends
the ``mod_logs`` row, emits the ``audit.action_recorded`` companion, and
fires ``EVT_MOD_ACTION``.

Forbidden in these files unless the receiver is ``moderation_service``:

* DB writes:       ``db.add_warning`` / ``db.clear_warnings`` /
                   ``db.log_mod_action``
* Discord actions: ``<member>.kick`` / ``.ban`` / ``.timeout``,
                   ``<guild>.ban`` / ``.unban``

Reads (``db.get_mod_logs``, ``db.get_warnings``) are allowed — this pins
the *write* path only.  ``services/moderation_service.py`` is the
legitimate writer and is intentionally NOT scanned.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

# Moderation adapter surfaces scanned by this invariant.
_SCANNED_DIRS = (
    _DISBOT / "cogs" / "moderation",
    _DISBOT / "views" / "moderation",
)
_SCANNED_FILES = (_DISBOT / "cogs" / "moderation_cog.py",)

# The only legitimate receiver for a moderation mutation in these files.
_ALLOWED_RECEIVER = "moderation_service"

_FORBIDDEN_DB_WRITES = {"add_warning", "clear_warnings", "log_mod_action"}
_FORBIDDEN_DISCORD_ACTIONS = {"kick", "ban", "unban", "timeout"}
_FORBIDDEN = _FORBIDDEN_DB_WRITES | _FORBIDDEN_DISCORD_ACTIONS


def _moderation_surface_files() -> list[Path]:
    files: list[Path] = []
    for d in _SCANNED_DIRS:
        if d.is_dir():
            files.extend(p for p in d.rglob("*.py") if "__pycache__" not in p.parts)
    files.extend(p for p in _SCANNED_FILES if p.exists())
    return sorted(set(files))


def _receiver_dotted(node: ast.expr) -> str:
    """Reconstruct the call receiver as a dotted string (``db``,
    ``moderation_service``, ``interaction.guild`` …)."""
    parts: list[str] = []
    rcv: ast.expr | None = node
    while isinstance(rcv, ast.Attribute):
        parts.append(rcv.attr)
        rcv = rcv.value
    if isinstance(rcv, ast.Name):
        parts.append(rcv.id)
    return ".".join(reversed(parts))


def _violations_in(tree: ast.AST) -> list[str]:
    found: list[str] = []
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
            continue
        if n.func.attr not in _FORBIDDEN:
            continue
        receiver = _receiver_dotted(n.func.value)
        # Allowed: the call routes through moderation_service.<action>.
        if receiver == _ALLOWED_RECEIVER or receiver.endswith(
            "." + _ALLOWED_RECEIVER,
        ):
            continue
        found.append(f"{receiver}.{n.func.attr}")
    return found


def test_moderation_surfaces_route_through_service():
    """No moderation adapter may mutate directly — route via the service."""
    violations: list[tuple[str, list[str]]] = []
    for path in _moderation_surface_files():
        tree = ast.parse(path.read_text(), filename=str(path))
        calls = _violations_in(tree)
        if calls:
            violations.append((str(path.relative_to(_REPO_ROOT)), calls))
    assert not violations, (
        "Moderation-convergence violation: direct moderation mutations outside "
        "services.moderation_service.\n"
        + "\n".join(f"  {p}: {calls}" for p, calls in violations)
    )


def test_scanned_surfaces_exist():
    """Keep the scan honest — if the surfaces move, update this invariant."""
    assert (
        _moderation_surface_files()
    ), "no moderation surface files found to scan — did the layout change?"
