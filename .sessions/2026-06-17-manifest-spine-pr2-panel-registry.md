# 2026-06-17 — Manifest spine PR2: panel registry + PanelManifest

> **Status:** `complete`

## Arc

Scheduled dispatch fire, **empty work order**. The night queue + BTD6-floor lane
are consumed/thinning and both open PRs (#941, #929) are `needs-hermes-review`-gated.
The live active thread is the **manifest spine** (Q-0162, owner-approved): PR1
(`CommandManifest`) shipped #1018, and `current-state.md` + the execution plan both
named **PR2 — panel registry + `PanelManifest`** as the next slice (the L3
panel-editor prerequisite). No claim on the lane → took it. Shipped as PR #1019.

## Shipped (PR #1019)

- **`core/runtime/panel_manifest.py`** (new) — typed `PanelManifest` /
  `PanelManifestEntry` / `PanelButton`, built **at startup from the persistent-view
  registry**. Design choice: the registry of `PersistentView` subclasses *is* the
  panel registry — those are exactly the panels with stable static custom_ids that
  survive restart (the manageable ones the L3 editor addresses). Each class is
  instantiated arg-free and its real components introspected, so the manifest records
  what the bot will actually render (mirrors PR1's "runtime truth, not AST"). 10
  panels / 67 buttons live.
- **`core/runtime/persistent_views.py`** — additive only: declarative `PANEL_ID`
  class var (defaults to `SUBSYSTEM`) + a faithful ordered enumeration
  (`iter_registered_view_classes`) so the **two `help` panels** — both registered
  under subsystem `"help"`, so collapsed in the subsystem-keyed recovery dict — both
  surface (`help:nav`, `help:categories`). Recovery behaviour unchanged.
- **`CommandManifestEntry.panels` back-populated** by a subsystem join
  (command.subsystem == panel.subsystem) via an optional `panels_by_subsystem` arg
  threaded through `build_command_manifest` / `build_and_cache_from_bot`. `actions`
  left deferred — there is no declared button→command binding yet, and the spine
  exists to eliminate *unverified* metadata, so honesty over fabrication.
- **Startup wiring** (`bot1.py`): panel manifest built before the command manifest
  (so the join sees it) + `panel_manifest` `startup_outcome` phase + smoke-checklist
  bullet. `panel_manifest` diagnostics provider.
- **Reconciliation test** (`tests/unit/runtime/test_panel_manifest.py`, +18): the
  vision doc's "panel registry vs view classes / custom IDs" check — every manifest
  button round-trips against a fresh re-instantiation of its view class; panel_ids
  unique; every registered class covered. +2 command-manifest join tests.

`check_quality --full` green (10414 passed) · `check_architecture --mode strict` 0
errors · mypy clean.

## Context delta

- **Needed and had:** the execution plan's PR2 spec + PR1's shape made this turn-key —
  I mirrored `command_manifest.py` almost structurally (frozen dataclasses, `to_dict`,
  build/cache/diagnostics, `_reset_for_tests`, isolation-hook registration).
- **Saved by probing first:** confirmed all registered `PersistentView`s instantiate
  arg-free and expose static custom_ids via `view.children` *before* committing to the
  introspection design — avoided a hand-maintained registry that would rot (the vision
  doc explicitly warns against that).
- **Found a latent issue:** the two `help` panels share subsystem `"help"`, so the
  recovery dict (`get_view_class`) only returns the last-registered one
  (`HelpCategoryView`). Not touched (anchor recovery is load-bearing + out of scope),
  but the manifest now surfaces both, and a future slice could split the help
  subsystem key. Flagged below.

## Flagged for maintainer

- **Latent (non-blocking):** `_REGISTRY` in `persistent_views.py` is keyed by
  `SUBSYSTEM`, and the two `help` panels both use `"help"` — so `get_view_class("help")`
  resolves to only one class (`HelpCategoryView`). Restart recovery for the other help
  panel may rely on it being re-created fresh rather than via the registry. Worth a look
  if help-panel restart ever misbehaves; the PanelManifest now makes the collision
  visible. Not fixed this session (recovery seam, out of PR2 scope).

## 💡 Session idea (Q-0089)

The PanelManifest now knows every panel's `subsystem`; the recovery registry silently
drops a panel when two share a subsystem (the `help` case above). A tiny invariant —
`test_no_subsystem_owns_two_persistent_panels_without_distinct_panel_ids` *plus* a
recovery-registry check that every registered class is reachable — would turn that
silent collapse into a CI signal, and is the natural sibling of the reconciliation test
shipped here. Filed under the manifest-spine reconciliation family; worth folding into
PR3 (which already adds the AST/ledger/export drift guards).

## ⟲ Previous-session review (Q-0102)

The previous run (#1018, manifest spine PR1) set this slice up almost perfectly: it
shipped the deferred `panels`/`actions` fields *shape-pinned but empty* and wrote a
clear "Next: PR2" pointer in both the ledger and the execution plan — so PR2 was a
straight continuation with zero re-derivation. The one thing it left implicit was *how*
the panel registry would be sourced (it said "panel registry" without naming the
persistent-view registry as the source); I had to probe to confirm that was the right,
non-rotting seam. **System improvement:** when a plan defers a field to a named future
PR, the plan PR should also name the *source seam* it expects that PR to draw from
(here: "PR2 sources panels from `core.runtime.persistent_views`"). I added that
specificity to the execution plan's PR2/PR3 entries so the next slice (PR3) inherits the
same turn-key clarity.

## Doc audit (Q-0104)

- Ledger: added the #1019 entry; updated the #1018 "Next: PR2" pointer to "shipped
  #1019". Pre-existing 4-PR ledger drift (SessionStart banner) left for the
  auto-reconciliation routine (Q-0124 — dispatch sessions don't run recon).
- Execution plan: PR2 marked ✅ SHIPPED with the as-built note + source-seam clarity.
- Smoke checklist: added the `panel_manifest` startup-phase bullet (CI-enforced 1:1 with
  `KNOWN_PHASES`).
- `check_docs` green; no new owner decisions.

## 📤 Run report

- **Did:** shipped manifest spine PR2 — the panel registry + typed `PanelManifest`
  (the L3 panel-editor prerequisite) · **Outcome:** shipped
- **Shipped:** #1019 (read-only metadata projection, no runtime behaviour change, no
  migration — self-merge on green)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none — auto-deploys on merge (no prod-check; read-only)
- **↪ Next:** manifest spine **PR3** — `GET /control/manifest` read (admin-gated,
  mirrors the Phase E reads #1013) + generate the manifest into the committed
  `dashboard/data/dashboard.json` export + the scanner-vs-ledger / committed-vs-fresh
  AST drift guards (makes AST a drift-detection layer). Fold in the recovery-registry
  collision invariant (session idea above). Plan:
  `planning/manifest-spine-execution-plan-2026-06-17.md` § PR3.
