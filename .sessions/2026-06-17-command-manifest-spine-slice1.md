# Session — manifest spine, slice 1 (typed CommandManifest over the ledger)

> **Status:** `in-progress`

## Context

Continuation of the same dispatch fire that shipped the global settings tier (#1017, merged). The
next ungated, owner-approved lane is the **manifest spine** — the dashboard vision doc's "key
structural investment" (`dashboard-vision-finalized-state.md` § "The manifest spine"). It is
**owner-decided BUILD IT** (Q-0162), its predecessor Phase E shipped (#1013), and its schema is
finalized (#998) — so this is a decided, approved architectural lane, not an ambiguous one.

Today command metadata comes from an AST scan (`scripts/scan_commands.py`) — fine for read-only docs,
fragile for management. The runtime already has a richer truth: `core/runtime/command_surface_ledger.py`
(classifications, visibility tier, aliases, declared-ness). The finalized answer is a **typed,
bot-owned manifest built at startup**, with AST demoted to drift-detection.

## Plan (this slice + the sequenced rest)

- **PR1 (this) — `CommandManifest` over the ledger.** A new `core/runtime/command_manifest.py` that
  projects the cached `CommandSurfaceLedger` into the typed #998 command schema, cached at startup +
  surfaced as a `command_manifest` diagnostics provider, with a manifest-faithfully-projects-ledger
  CI invariant (the first "reconciliation test that makes the metadata trustworthy"). Additive,
  offline-testable, changes no existing behavior.
- **PR2 — panel registry + `PanelManifest`** (declarative panel descriptors beside the view classes;
  the prerequisite for the L3 panel-layout editor).
- **PR3 — control-API `GET /control/manifest` read + `dashboard.json` export + scanner-vs-ledger
  reconciliation drift guard** (AST becomes drift-detection).
- **PR4 — the panel-layout editor (H / L3 "move buttons")** the spine unblocks.

Full plan: `docs/planning/manifest-spine-execution-plan-2026-06-17.md`.

## What shipped

(filled in as the work lands)
