# Session — global settings tier (per-guild → global → default)

> **Status:** `in-progress`

## Context

Empty scheduled dispatch fire (no work order) → advance the next plan slice. The BTD6
deterministic-floor lane is thinning (current-state ▶ NIGHT QUEUE) and the **developer-dashboard
thread is the active lane**. Its next *pure-code, ungated* runtime slice is the one the live-editor
plan names explicitly: **the global-settings tier** (`dashboard-live-editor-plan.md`
§ "Settings editor — global + per-server", phase ②). The owner asked: *"as bot owner let me change
things globally, as well as per-server."* Today `services.settings_resolution.resolve_setting` is
**per-guild only** (per-guild KV row → spec default); there is **no global layer** — exactly the gap
`core/runtime/feature_flags.py` already solved with per-guild → global → default. This session mirrors
that proven pattern for `SettingSpec` scalars.

## Plan (2 focused PRs — the plan's "risky-runtime rule" isolates the hot-path read change)

- **PR 1 (this one) — resolution read tier.** `resolve_setting` gains a global tier: after a
  per-guild miss, read the global row (`guild_id = 0`, the repo's global sentinel — already used by
  the mining store) before falling back to the spec default. New provenance `"global_kv"`; an
  `include_global` flag (default on) so the mutation pipeline's `_read_previous` stays scope-local
  (byte-identical per-guild write audit). Dormant in practice until PR 2 writes a global row.
- **PR 2 — owner-gated global write scope.** `SettingsMutationPipeline.set_value` gains a
  `scope="global"` path, owner-gated (`config.BOT_OWNER_USER_ID`), writing/auditing the `guild_id=0`
  row through the existing audited seam. Activates the tier.

Both: `check_quality --full` green · `check_architecture --mode strict` 0 · new tests that fail
against pre-change behavior.

## What shipped

(filled in as the work lands)
