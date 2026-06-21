"""Role-threshold writer-convergence invariant (Adaptive Setup P0C — COMPLETE).

Sibling to ``test_no_direct_role_mutations.py`` (which pins role *object*
create/edit/delete). This one fences the **threshold writes**: the role command
+ view surface must NOT call the ``utils.db.roles`` threshold mutation
primitives **directly** — it routes through the audited
``services.role_automation`` seam (which does the identical DB write **plus**
the ``audit.action_recorded`` emit and the XP-cache invalidation), so a
profile/routine compiler has one canonical seam for role-threshold changes —
see ``docs/ownership.md`` § "Direct vs. draft mutation lanes" and
``docs/planning/adaptive-setup-access-routine-platform-2026-06-08.md`` §16.5.

**P0C shipped 2026-06-08:** all six original direct *setter* sites
(``time_roles_panel`` Seed-Defaults + ``TimeDaysModal``, ``creation_panel``
``RoleAutomationModal``, ``_helpers._ensure_defaults``, ``xp_roles_panel``
``XpLevelModal``, and ``role_cog.setrole``) were converted, so
``_ALLOWED_DIRECT_THRESHOLD_FILES`` is now **empty** and this invariant is the
absolute rule: *no direct threshold writes anywhere in the role surface*.
(*2026-06-21:* the ``Seed-Defaults`` button + ``_helpers._ensure_defaults`` were
later **removed** — roles load dynamically now — and the Time panel's new
``Clear Missing`` purge routes through the audited
``role_automation.clear_time_threshold`` seam, so the fence still holds.) It
began as a *shrinking ratchet* — the allowlist pinned the known-remaining sites
and forbade new drift; emptying it is how P0C records "done". A **new** direct
write in any scanned file now fails immediately.

**Widened to clears 2026-06-10 (consolidated plan Batch 3, FIND-RS06):** the
fence originally named only the setters, so the three field-specific *clear*
call sites (``xp_roles_panel`` remove-select, ``time_roles_panel``
remove-select, ``role_cog.unsetrole``) bypassed the seam unaudited.  Those now
route through ``role_automation.clear_time_threshold`` /
``clear_xp_threshold``, and the fence covers every threshold mutation
primitive — setters, field-specific clears, and the full-row
``remove_role_threshold`` (currently zero callers; fenced so a new one cannot
appear unaudited).
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

_SCANNED_FILES = (_DISBOT / "cogs" / "role_cog.py",)
_SCANNED_DIRS = (_DISBOT / "views" / "roles",)

# Direct DB threshold mutation primitives that must converge on the audited
# role_automation seam — setters, field-specific clears, and the full-row
# delete. (The seam itself lives in services/role_automation.py, which is NOT
# in the scanned surface, so its own internal db calls are correctly excluded.)
_DIRECT_THRESHOLD_WRITERS = {
    "set_role_threshold",
    "set_role_xp_threshold",
    "clear_role_time_threshold",
    "clear_role_xp_threshold",
    "remove_role_threshold",
}

# P0C is COMPLETE (2026-06-08): all six role-threshold write sites now route
# through services.role_automation.set_{time,xp}_threshold, so the allowlist is
# empty and the invariant is the absolute rule — *no* direct threshold write
# anywhere in the role command/view surface. A new direct write in any scanned
# file now fails immediately. (Re-adding a file here would only mask a fresh
# regression; convert the write instead.)
_ALLOWED_DIRECT_THRESHOLD_FILES: frozenset[str] = frozenset()


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
        "New direct role-threshold mutation(s) — route these through the "
        "audited services.role_automation seam (set_time_threshold / "
        "set_xp_threshold / clear_time_threshold / clear_xp_threshold), do "
        "not call the utils.db.roles threshold primitives directly: "
        f"{sorted(new_drift)}"
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
    # Batch 3 (RS06): the clear lane has an audited seam too.
    assert "async def clear_time_threshold(" in src
    assert "async def clear_xp_threshold(" in src
    # ...and it actually emits the audit companion (not a silent write).
    assert "emit_audit_action(" in src


def test_scanned_surfaces_exist():
    """Keep the scan honest — if the role surface moves, update this invariant."""
    assert _role_surface_files(), "no role surface files found — did the layout change?"
