# Session — manifest spine, slice 1 (typed CommandManifest over the ledger)

> **Status:** `complete`

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

## What shipped (PR #1018)

- **`core/runtime/command_manifest.py`** — typed `CommandManifest` / `CommandManifestEntry` (the
  #998 schema), built as a **pure projection** of the cached `CommandSurfaceLedger` (reuses it — no
  second surface walk). Carries every ledger-known field (`qualified_name`, `kind`, `cog`,
  `subsystem`, `classification` + `classification_declared`, `visibility_tier`, `aliases`,
  `discord_hidden`, `runtime_verified`) + a `to_dict()` export; deferred fields
  (`source`/`panels`/`actions`/`related_settings`/`capability_required`) are shape-pinned but empty.
  Startup-cached + a `command_manifest` diagnostics provider (immediate operator consumer).
- **Startup wiring (`bot1.py`)** right after the ledger build, non-fatal, `startup_outcome`-tracked.
- **CI invariant** `test_command_manifest.py` (8 tests) — manifest-faithfully-projects-ledger (count
  parity, `qualified_name`, field mapping, `to_dict()` schema, cache round-trip, diagnostics).
- **Pinned-surface cascade:** `KNOWN_PHASES` + smoke checklist (new `command_manifest` phase),
  `tests/_isolation.py` reset-hook classification, the execution plan linked from the vision doc.
- **`docs/planning/manifest-spine-execution-plan-2026-06-17.md`** — the Q-0162 spine sequenced into
  PR1 (this) → PR2 panel registry → PR3 control-API read + dashboard export + AST drift guard → PR4
  panel-layout editor.

`check_quality --full` green (10397 passed) · `check_architecture --mode strict` 0 errors.
**Merge gate:** self-merge on green (Q-0113) — additive, behavior-neutral, owner-approved lane.

## 💡 Session idea (Q-0089) — promote the AST scanner into a CI drift guard against the manifest

This slice makes the runtime manifest the source of truth and the vision doc demotes
`scripts/scan_commands.py` (AST) to "drift detection only" — but that demotion is currently *aspirational*:
there's no test yet that fails when the AST scan and the runtime manifest disagree. The idea (slated as
PR3, but worth flagging as genuinely high-value): a CI test that runs the AST scanner and asserts its
command set reconciles with a committed manifest snapshot, so a command renamed/moved in code without a
matching manifest refresh *fails CI* — turning "two sources that might silently diverge" into "one of
them is authoritative and the other is a guard." It's the structural payoff that makes the whole spine
trustworthy, and it's the cheapest way to keep the AST honest as the manifest grows.

## ⟲ Previous-slice review (Q-0102)

The immediately-previous slice this session (#1017, the global settings tier) went well — it shipped a
complete read+write feature with 18 tests and correctly reasoned about *not* forcing a 2nd slice when
the remaining lanes looked gated. **The miss it had, in hindsight:** it concluded "the dashboard's next
ungated slice is gated (phase ③ owner-paced)" and handed off toward a *different* lane — but it didn't
notice that the **manifest spine** (a *different* dashboard sub-lane, owner-approved Q-0162, Phase-E
predecessor shipped) was both ungated AND buildable. So its handoff slightly undersold the available
work. **System improvement (initiated):** when a session decides "the active lane's next slice is
gated," it should scan the lane's *sibling* sub-lanes (the vision doc's decision table / phase rows)
before concluding the whole lane is blocked — a gated headline phase doesn't mean every sub-lane is
gated. I acted on exactly that this run: re-reading the vision doc's Q-0162 decision row surfaced the
manifest spine as the genuine next buildable slice. Worth wiring into `/session-close` as a "did you
check sibling sub-lanes?" prompt when a handoff declares a lane blocked.

## 📋 Documentation audit (Q-0104)

- The new lane is in its durable homes: the execution plan (linked from the vision doc, no orphan), the
  vision doc's reviewer/decision references, and the current-state ledger entry for #1018.
- No new owner *decision* this run (Q-0162 already approved the spine); no new router Q-block needed.
- The SessionStart banner flagged the ledger ~5 PRs behind; that cross-cutting reconcile is the
  auto-firing docs-reconciliation routine's job (Q-0124) — I added only my own #1018 entry.
- Nothing from this session lives only in chat.

## Handoff (▶ next)

The manifest spine's **PR2 (panel registry + `PanelManifest`)** is the next slice — ungated, bot-owned,
and the prerequisite for the L3 panel-layout editor. It composes the view classes into declarative
panel descriptors (`panel_id` / `view_class` / `buttons[]` with `action_id`/`custom_id`/`label`/`row`/
`command`) and back-populates `CommandManifestEntry.panels` / `.actions` (shape already reserved). Then
PR3 (control-API `GET /control/manifest` read + `dashboard.json` export + the AST drift guard above).
Full sequence + turn-key detail: `docs/planning/manifest-spine-execution-plan-2026-06-17.md`.
