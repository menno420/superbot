# Manifest spine PR3 — control-API manifest read + cross-manifest reconciliation

> **Status:** `in-progress`
> **Branch:** `claude/magical-rubin-bq71go`
> **Dispatch:** scheduled fire, empty work order → advanced the live ▶ Next slice (manifest spine
> PR3, owner-approved Q-0162; PR1 #1018 + PR2 #1019 shipped).

## What I'm about to do

Ship the next manifest-spine slice — make the typed manifest **readable over the live control API**
and **self-reconciling** (the spine's stated core purpose: turn AST-classified panel metadata into
*verified* metadata):

1. **`GET /control/manifest`** on the dormant control API — token-only (global data, mirrors
   `/control/help/catalogue`), serving `CommandManifest.to_dict()` + `PanelManifest.to_dict()`; builds
   on demand from the bot when the startup cache is empty. + a thin `control_client.get_manifest()`.
2. **Cross-manifest reconciliation** — a pure `manifest_reconciliation` projection: a
   `panel_action`-classified command whose subsystem owns **no** registered panel is a
   `dangling_panel_action` finding. Surfaced in `CommandManifest.to_dict()["findings"]` (was reserved
   `[]`) + the `command_manifest` diagnostics snapshot, so the live read carries its own trust signal.
3. **CI drift guard** — the cheap, non-flaky "AST is drift-detection" test: the AST
   `scan_commands` `panel_action` subsystems ⊆ the runtime `PanelManifest` subsystems (verified to
   hold today: panel_action subs = {mining, moderation, role}, all have panels).

**Deferred honestly to PR4** (no declared button→command binding yet — a name-level guard would be
false-positive-prone, Q-0120): per-button `command` binding + the button-level
`panel_action`↔button reconciliation. The dashboard.json manifest export stays the AST `cogs` view
(the export can't import disbot); the live truth is `/control/manifest`.

## Verification
`python3.10 scripts/check_quality.py --full` green · `check_architecture --mode strict` 0 · new
reconciliation + endpoint tests.
