# Manifest spine PR3 — control-API manifest read + cross-manifest reconciliation

> **Status:** `complete`
> **Branch:** `claude/magical-rubin-bq71go` · **PR #1020** (auto-merge armed on green)
> **Dispatch:** scheduled fire, empty work order → advanced the live ▶ Next slice (manifest spine
> PR3, owner-approved Q-0162; PR1 #1018 + PR2 #1019 shipped).

## What shipped

Made the typed manifest **readable over the live control API** and **self-reconciling** — the spine's
stated core purpose: turn AST-classified panel metadata into *verified* metadata.

1. **`GET /control/manifest`** (`disbot/control_api.py`) — token-only (global data, mirrors
   `/control/help/catalogue`), serves `CommandManifest.to_dict()` + `PanelManifest.to_dict()`; uses the
   startup cache, builds on demand from the bot when empty. + `dashboard/control_client.get_manifest()`.
2. **`disbot/core/runtime/manifest_reconciliation.py`** — a pure projection over the command manifest:
   a `panel_action`-classified command whose subsystem owns **no** registered panel is a
   `dangling_panel_action` finding. Surfaced in `CommandManifest.to_dict()["findings"]` (was reserved
   `[]`) + the `command_manifest` diagnostics snapshot (`finding_count`/`findings`).
3. **CI drift guard** (`tests/unit/runtime/test_manifest_drift.py`) — the cheap, non-flaky
   "AST-is-drift-detection" check: AST `scan_commands` `panel_action` subsystems ⊆ runtime
   `PanelManifest` subsystems. Holds today ({mining, moderation, role} all have panels). Includes a
   guard-the-guard test so it can't pass vacuously.
4. **Deploy-SHA freshness badge** — `command_manifest.deploy_build_sha()` reads
   `RAILWAY_GIT_COMMIT_SHA` (short 12); `build_and_cache_from_bot` defaults `bot_build` to it, so the
   live read is cache-bustable / freshness-badged without every call site threading it.

`check_quality --full` green (10431, +16 tests) · `check_architecture --mode strict` 0 · env-vars doc
regenerated (new `RAILWAY_GIT_COMMIT_SHA` ref).

## Decisions / what I deviated from the plan on

- **Name-level `panel_action`↔button reconciliation deferred to PR4.** Verified against live data
  (Q-0120 — never assert a guard that fights the evidence): `panel_action` command *names* do NOT map
  to button `action_id` suffixes (`createrole` cmd vs `role:create` button). No declared button→command
  binding exists yet, so a strict name-level guard would be ~false-positive. PR4 declares the binding
  first, then the button-level check is real. The clean, holds-today reconciliation is **subsystem-level**.
- **dashboard.json manifest export dropped from PR3.** The export script can't import disbot, so the
  committed JSON stays the AST `cogs` view; the live truth is `/control/manifest`. Adding a runtime
  manifest to the committed export would require the export to run the bot — wrong layer.
- The reconciliation reads `entry.panels` (already back-populated by PR2's subsystem join), so findings
  need no second walk and no panel-manifest argument — a clean consequence of PR2's design.

## Handoff — next agent (▶ Next action is already sharpened in current-state)

The manifest spine's **pure ungated read-code is exhausted.** Remaining = **PR4: the panel-layout
editor** (H / L3 "move buttons") — a *declared* button→command binding across every persistent view +
button-level reconciliation + a DB-backed layout overlay + the website editor. PR4 is **owner-paced**
(control-API *write* surface, needs `CONTROL_API_TOKEN`) **and architecturally significant** (the
binding can't be inferred — must be declared per view). A future empty fire should plan PR4 with the
owner on write-side pacing, or take a different ungated lane (BTD6 floor candidates are thinning;
image-mod #941 + security #929 are Hermes-gated).

## 🐞 Finding (recorded, not fixed here)

`dashboard/data/dashboard.json` is **~300 lines stale on main** — a fresh `export_dashboard_data.py`
run differs (env line-numbers + accumulated ideas/sessions/bugs from parallel sessions). There is **no
committed-vs-fresh freshness guard** (`check_dashboard_data.py` validates structure/counts only). I did
NOT regenerate it in this PR — it pulls unrelated parallel-session churn into a focused PR and a strict
byte-equality guard would constantly redden CI across the ~6 sessions that touch it. Better owned by
the docs-reconciliation routine. See 💡 below.

## 💡 Session idea (Q-0089)

**dashboard.json freshness — make the docs-reconciliation routine regenerate it each pass, + a *soft*
structural-drift reporter.** The committed `dashboard.json` is a generated artifact that silently
drifts (hit this directly — 300 lines stale on main). Two-part: (a) the reconciliation routine runs
`export_dashboard_data.py` as part of its docs pass (it already touches the source docs), keeping it
fresh on cadence without burdening every session; (b) extend `check_dashboard_data.py` with a
**non-blocking** structural-drift reporter — compare committed vs a fresh export on the *structural*
keys only (cog/command set, env-var set, setting keys — NOT timestamps/build-SHA/ideas-churn) and emit
a soft warning, so a *real* surface drift (a new cog/command/env-var never exported) is caught without
the fragility of byte-equality. Genuinely believe in it — it's the missing half of the manifest spine's
own "AST is drift-detection" philosophy applied to the committed export.

## ⟲ Previous-session review (Q-0102)

The previous run (#1019, manifest spine PR2) did the spine a real favour: by **back-populating
`CommandManifestEntry.panels` via the subsystem join in PR1's `build_and_cache_from_bot`**, it made
*this* session's reconciliation trivial — the `dangling_panel_action` finding is a pure read of
`entry.panels`, no second walk, no cross-module plumbing. Clean forward-compatible design.

**What it (and the plan) could have done better → a workflow improvement:** the manifest-spine
execution plan states PR3 should assert "every `panel_action` command maps to a real button" as if it
were straightforward — but at name-level that's **false today** (I had to prototype against live data
to discover it). **Improvement: an execution plan that schedules a *guard/assertion* should carry an
explicit "verify this holds against ground truth before asserting it" caveat** — the Q-0120 principle
("a check that fights the evidence is a bug in the check") applied at *plan-authoring* time, not just at
guard-writing time. Saves the next agent from shipping a false-positive guard because the plan said so.
(Captured here, not promoted — it's a refinement to plan-authoring convention, not a CLAUDE.md rule.)
