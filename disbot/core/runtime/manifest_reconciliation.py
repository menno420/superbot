"""Manifest reconciliation — slice 3 of the dashboard manifest spine (Q-0162).

The spine exists to turn *unverified* command/panel metadata into **verified**
metadata: an AST scan can only answer "does this *look* like a panel command?",
while the runtime manifests know which commands are classified ``panel_action``
and which panels actually exist. This module is the reconciliation seam between
them — it cross-checks the :class:`~core.runtime.command_manifest.CommandManifest`
against the :class:`~core.runtime.panel_manifest.PanelManifest` and reports
**findings** (drift) the live read (``GET /control/manifest``) and ``!platform``
diagnostics surface.

This slice ships the reconciliation that holds cleanly **today**:

* ``dangling_panel_action`` — a command classified ``panel_action`` (declared to
  be invoked from a panel button) whose **subsystem owns no registered panel** in
  the PanelManifest. That command's panel action has nowhere to live, which is a
  real structural drift. (The command manifest already back-populates each
  command's ``panels`` from the panel manifest by subsystem, so the check is a
  pure read of ``entry.panels``.)

Deferred to a later slice (no declared button→command binding yet, so a stricter
check would be false-positive-prone — the CLAUDE.md Q-0120 rule): the
**button-level** reconciliation (every ``panel_action`` command maps to a *real
button*, and every button's ``command`` points at a real command). ``panel_action``
command *names* deliberately do not equal button ``action_id`` suffixes today
(``createrole`` vs ``role:create``), so that check waits for the binding.

Pure and side-effect-free: every function takes manifests and returns data. No
module-level imports of ``services`` (mirrors the manifest modules' cycle
discipline) — this module imports only its sibling manifest types.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.runtime.command_manifest import CommandManifest

# Finding kinds (stable strings — consumers gate on them).
DANGLING_PANEL_ACTION = "dangling_panel_action"


@dataclass(frozen=True)
class ReconciliationFinding:
    """One cross-manifest drift finding.

    ``kind`` is one of the module's finding-kind constants; ``command`` /
    ``subsystem`` locate it; ``detail`` is a human-readable one-liner.
    """

    kind: str
    command: str
    subsystem: str | None
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "command": self.command,
            "subsystem": self.subsystem,
            "detail": self.detail,
        }


def reconcile(manifest: CommandManifest) -> tuple[ReconciliationFinding, ...]:
    """Cross-check ``manifest`` against the panel join it already carries.

    Returns the findings (empty when clean). A ``panel_action``-classified
    command with no ``panels`` (its subsystem owns no registered panel) is a
    :data:`DANGLING_PANEL_ACTION` finding — the command claims to be a panel
    button's action but no panel backs it.

    Pure: reads only the command entries' ``classification`` / ``panels`` (the
    latter back-populated by ``command_manifest`` from the panel manifest by
    subsystem), so it needs no second walk and no panel-manifest argument.
    """
    findings: list[ReconciliationFinding] = []
    for entry in manifest.commands:
        if entry.classification == "panel_action" and not entry.panels:
            findings.append(
                ReconciliationFinding(
                    kind=DANGLING_PANEL_ACTION,
                    command=entry.qualified_name,
                    subsystem=entry.subsystem,
                    detail=(
                        f"command {entry.qualified_name!r} is classified "
                        f"'panel_action' but its subsystem "
                        f"({entry.subsystem!r}) owns no registered panel"
                    ),
                ),
            )
    return tuple(findings)


def reconcile_to_dicts(manifest: CommandManifest) -> list[dict[str, Any]]:
    """:func:`reconcile` as a list of plain dicts (the export / API shape)."""
    return [f.to_dict() for f in reconcile(manifest)]


__all__ = [
    "DANGLING_PANEL_ACTION",
    "ReconciliationFinding",
    "reconcile",
    "reconcile_to_dicts",
]
