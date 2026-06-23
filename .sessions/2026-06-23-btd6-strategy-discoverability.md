# 2026-06-23 — Discoverability U4: surface `!btd6strat` (BTD6 Strategy button)

> **Status:** `in-progress` — continuing the discoverability audit after Session 1 (#1370) + the
> Phase-0 fleet rails (#1371). Fixes one of the two recorded reachability gaps as fleet unit **U4**
> ([fleet plan](../docs/planning/consolidation-fleet-plan-2026-06-23.md)). Born-red card; flip to
> `complete` last → auto-merge on green. No active coordinator/fleet (0 open PRs), so this self-merges
> per the standing workflow.

> **Run type:** `manual · continuation` (next startable item after the merged foundation)

## What I'm about to do

The `!btd6strat` gap: `BTD6StrategyCog` maps to no registered subsystem and the BTD6 hub panel had no
Strategy button, so the member-facing strategy *browse* surface was unreachable by clicking through
`!help` (verified in Session 1's gap ledger). Fleet plan U4: **add a Strategy child to `BTD6PanelView`**
(bespoke hand-built panel) mirroring its Live-Events/Towers buttons — opens the strategy browse embed
(`views.btd6.strategy_browse.build_browse_embed`, the same surface as `!btd6strat browse`) ephemerally.
Then allowlist `btd6strat` as reachable-via-panel (source-cited) and drop it from the guard's `_BASELINE`
(2 → 1), keeping the guard honest + the ratchet shrinking.

Contained to btd6 files (U4's territory) + the guard allowlist/baseline. Also GC'd the stale merged claim
`claude__phase0-completion.md` (#1371).

## Also noting (drift-on-sight, for whoever builds Phase 0.5)

The fleet plan's Phase-0.5 settings-orphan guard says to use `core.runtime.subsystem_schema.all_schemas()`
"(offline)" — but **it returns `{}` offline** (schemas register at `cog_load`, runtime). The static
alternative is the per-subsystem `disbot/utils/settings_keys/<x>.py` files (+ AST `register_schemas` call
sites). Recorded so Phase 0.5 isn't built on the empty source.
