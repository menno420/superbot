# Manifest spine — execution plan (2026-06-17)

> **Status:** `plan` — sequences the **owner-approved** (Q-0162: *"Build it"*) manifest spine into
> modular, buildable PRs. The destination + schema are finalized in
> [`dashboard-vision-finalized-state.md`](dashboard-vision-finalized-state.md) § "The manifest spine"
> (synthesizing the owner's deep-research report + Codex #998); this doc is the *how/when*, not the
> *what*. Where they differ on shape, the vision doc wins.

## Why a spine (the decided rationale)

Command/panel metadata today comes from an AST scan (`scripts/scan_commands.py`) — fine for read-only
docs, fragile for *management*: it answers "does this *look* like a panel command?" not "*which*
button, in *which* panel, backing *which* command, with *what* authority?". The runtime already holds a
richer truth in `core/runtime/command_surface_ledger.py` (classification, visibility tier, aliases,
declared-ness). The finalized answer: a **typed, bot-owned manifest built at startup** from runtime
registrations + classifications + (later) panel registry + schema bindings, with the AST demoted to a
**drift-detection layer**. The manifest gates *command-management trustworthiness* and the panel editor
(H) — not the settings/help/routing editors, which ride already-typed seams (reviewer note R2, Q-0162).

## Sequenced PRs (modular, not over-segmented)

### PR1 — `CommandManifest` over the ledger ✅ SHIPPED (#1018)

`core/runtime/command_manifest.py` projects the cached `CommandSurfaceLedger` into the typed #998
command schema (`qualified_name`, `kind`, `cog`, `subsystem`, `classification` +
`classification_declared`, `visibility_tier`, `aliases`, `discord_hidden`, `runtime_verified`), with a
`to_dict()` export, startup caching (mirrors the ledger), a `command_manifest` diagnostics provider,
and the **manifest-faithfully-projects-ledger** CI invariant (the first of the vision doc's
reconciliation tests). Deferred fields (`source`, `panels`, `actions`, `related_settings`,
`capability_required`) are present-but-empty so the shape is stable as the spine grows.

### PR2 — panel registry + `PanelManifest` ✅ SHIPPED (#1019)

`core/runtime/panel_manifest.py` projects the **persistent-view registry** (the panels with stable
static custom_ids that survive restart — exactly the manageable ones) into a typed `PanelManifest`,
built **at startup from the runtime registry** (mirroring PR1's "runtime truth, not AST"). Each
registered `PersistentView` is instantiated arg-free and its real components are introspected into
`PanelButton`s (`action_id`/`custom_id`/`label`/`row`; `command` deferred — no declared button→command
binding yet). `persistent_views.py` gained a declarative `PANEL_ID` class var + a faithful ordered
enumeration (`iter_registered_view_classes`) so the two `help` panels (collapsed in the subsystem-keyed
recovery dict) both surface. `CommandManifestEntry.panels` is back-populated by a subsystem join
(`actions` stays deferred). The **panel-registry-vs-view-classes** reconciliation test
(`tests/unit/runtime/test_panel_manifest.py`) round-trips every manifest button against a fresh
instantiation of its view class. Deferred: per-panel `source` (file/line, PR3 AST join), `layout_source`
flips to `db_overlay` in PR4.

### PR3 — control-API `manifest` read + `dashboard.json` export + AST drift guard

- `GET /control/manifest` on the dormant control API (admin-gated, mirrors the Phase E read endpoints
  shipped in #1013) serving `CommandManifest.to_dict()` (+ `PanelManifest`).
- Generate the manifest into the committed `dashboard/data/dashboard.json` export (via a scanner/export
  script), so the decoupled site reads the bot's truth.
- The **scanner-vs-ledger / committed-export-vs-fresh-export** reconciliation drift guards (CI) that
  make AST a drift-detection layer rather than a source of truth.
- Join `source` (file/line) from the AST scanner; join `related_settings` / `capability_required` from
  `SettingSpec` / capability bindings.
- **Cross-manifest reconciliation (the manifest's core purpose):** reconcile the command ledger's
  `panel_action` classification against the PanelManifest's real button `action_id`s — every
  `panel_action`-classified command should map to a real button, and (once the button→command binding
  lands) every button's `command` should point at a real command. This is the test that turns "looks
  like a panel command" into a *verified* "this button backs this command" — the AST `button_backed`
  weakness the spine exists to close. Source seam for PR2's panel data: `core.runtime.persistent_views`
  (the persistent-view registry — the panels with stable static custom_ids).

### PR4 — the panel-layout editor (H / L3 "move buttons")

The DB-backed panel-layout overlay + the website editor the spine unblocks (the second half of L3).
Owner-paced like the other control-API *write* surfaces (needs the `CONTROL_API_TOKEN`); plan
separately once PR2–PR3 land.

## Verification (every slice)

`python3.10 scripts/check_quality.py --full` green · `check_architecture --mode strict` 0 errors ·
the new reconciliation test for that slice fails against pre-change behavior.

## Notes / open follow-ups

- `bot_build` in the manifest envelope is empty in PR1 — PR3 should source it from the deploy SHA
  (`RAILWAY_GIT_COMMIT_SHA`) so the export is cache-bustable / freshness-badged.
- The manifest reuses the **cached** ledger (no second surface walk); PR2's panel registry should
  likewise compose, not re-walk.
