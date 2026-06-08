"""Role-threshold writer-convergence drift fence (Adaptive Setup P0C).

Sibling to ``test_no_direct_role_mutations.py`` (which pins role *object*
create/edit/delete). This one fences the **threshold writes**: the role command
+ view surface still calls ``utils.db.roles.set_role_threshold`` /
``set_role_xp_threshold`` **directly**, bypassing the audited
``services.role_automation.set_time_threshold`` / ``set_xp_threshold`` seam
(which does the identical DB write **plus** the ``audit.action_recorded`` emit
and the XP-cache invalidation). Until those panels route through the service,
a profile/routine compiler has no single canonical seam for role-threshold
changes — see ``docs/ownership.md`` § "Direct vs. draft mutation lanes" and
``docs/planning/adaptive-setup-access-routine-platform-2026-06-08.md`` §16.5.

**This is a shrinking ratchet, not a permanent allowlist.** Each file below is a
known P0C target. As a panel is converted to the audited seam, **remove its
filename from ``_ALLOWED_DIRECT_THRESHOLD_FILES``** (the test fails until you
do, which keeps the punch list honest). When the set is empty, the invariant
becomes the absolute rule: *no direct threshold writes anywhere in the role
surface*. A **new** direct write in any non-listed file fails immediately, so
the drift can never grow while P0C is pending.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

_SCANNED_FILES = (_DISBOT / "cogs" / "role_cog.py",)
_SCANNED_DIRS = (_DISBOT / "views" / "roles",)

# Direct DB threshold writers that must converge on the audited role_automation
# seam. (The seam itself lives in services/role_automation.py, which is NOT in
# the scanned surface, so its own internal db call is correctly excluded.)
_DIRECT_THRESHOLD_WRITERS = {"set_role_threshold", "set_role_xp_threshold"}

# Known P0C targets — files that still write a threshold directly today.
# SHRINK this set as each panel is routed through role_automation. Empty = done.
_ALLOWED_DIRECT_THRESHOLD_FILES: frozenset[str] = frozenset(
    {
        "time_roles_panel.py",
        "creation_panel.py",
        "_helpers.py",
        "xp_roles_panel.py",
        "role_cog.py",
    },
)


def _role_surface_files() -> list[Path]:
    files: list[Path] = []
    for d in _SCANNED_DIRS:
        if d.is_dir():
            files.extend(p for p in d.rglob("*.py") if "__pycache__" not in p.parts)
    files.extend(p for p in _SCANNED_FILES if p.exists())
    return sorted(set(files))


def _direct_threshold_calls(tree: ast.AST) -> int:
    """Count ``X.set_role_threshold(...)`` / ``X.set_role_xp_threshold(...)``
    *calls* (AST-level, so a log-string mentioning the name does not count).
    """
    count = 0
    for n in ast.walk(tree):
        if (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr in _DIRECT_THRESHOLD_WRITERS
        ):
            count += 1
    return count


def _files_with_direct_threshold_writes() -> dict[str, int]:
    out: dict[str, int] = {}
    for path in _role_surface_files():
        tree = ast.parse(path.read_text(), filename=str(path))
        n = _direct_threshold_calls(tree)
        if n:
            out[path.name] = n
    return out


def test_no_new_direct_threshold_write_drift():
    """The set of role-surface files writing thresholds directly must equal the
    documented P0C target list — no new file may join it, and a converted file
    must be removed from the allowlist.
    """
    offending = _files_with_direct_threshold_writes()
    offending_files = set(offending)

    new_drift = offending_files - _ALLOWED_DIRECT_THRESHOLD_FILES
    assert not new_drift, (
        "New direct role-threshold write(s) — route these through "
        "services.role_automation.set_time_threshold / set_xp_threshold "
        "(audited seam), do not call utils.db.roles.set_role_threshold* "
        f"directly: {sorted(new_drift)}"
    )

    converted = _ALLOWED_DIRECT_THRESHOLD_FILES - offending_files
    assert not converted, (
        "These files no longer write thresholds directly (P0C progress!) — "
        "remove them from _ALLOWED_DIRECT_THRESHOLD_FILES to keep the punch "
        f"list honest: {sorted(converted)}"
    )


def test_audited_threshold_seam_exists():
    """Positive check — the canonical audited seam the panels must converge on
    is present, so the P0C refactor has a real target.
    """
    src = (_DISBOT / "services" / "role_automation.py").read_text()
    assert "async def set_time_threshold(" in src
    assert "async def set_xp_threshold(" in src
    # ...and it actually emits the audit companion (not a silent write).
    assert "emit_audit_action(" in src


def test_scanned_surfaces_exist():
    """Keep the scan honest — if the role surface moves, update this invariant."""
    assert _role_surface_files(), "no role surface files found — did the layout change?"
