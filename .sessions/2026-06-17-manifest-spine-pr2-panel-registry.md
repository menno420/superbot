# 2026-06-17 — Manifest spine PR2: panel registry + PanelManifest

> **Status:** `in-progress`

## What I'm about to do

Scheduled dispatch fire, empty work order → advance the live active thread. The
**manifest spine** (Q-0162, owner-approved) shipped PR1 (`CommandManifest`, #1018);
`current-state.md` + the execution plan name **PR2 — panel registry + `PanelManifest`**
as the next slice (the L3 panel-editor prerequisite). Both open PRs (#941, #929) are
`needs-hermes-review`-gated; no claim on the manifest lane.

Building (CLASS: feature, dispatched → no phase gate; ungated, read-only metadata):

- `core/runtime/panel_manifest.py` — typed, bot-owned `PanelManifest` built **at
  startup from the persistent-view registry** (the runtime-truth source, mirroring how
  PR1 built `CommandManifest` from the ledger, not AST). One `PanelManifestEntry` per
  registered `PersistentView`, `PanelButton[]` introspected from the real components
  (`action_id`/`custom_id`/`label`/`row`/`command`).
- `core/runtime/persistent_views.py` — additive: declarative `PANEL_ID` class var +
  faithful ordered enumeration (`iter_registered_view_classes`) so the two `help`
  panels (collapsed in the subsystem-keyed recovery dict) both appear.
- Back-populate `CommandManifestEntry.panels` by subsystem join (actions stay deferred
  — no declared button→command binding yet; honesty over fabrication).
- Wire into `bot1.py` startup; `panel_manifest` diagnostics provider + startup_outcome.
- Reconciliation test: panel registry vs view classes / custom IDs.

`check_quality --full` + `check_architecture --mode strict` green before flip to ready.
