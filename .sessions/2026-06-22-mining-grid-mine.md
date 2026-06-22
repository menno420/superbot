# 2026-06-22 — Mining grid Mine (hub-redesign PR 3)

> **Status:** `complete` — grid Mine shipped; PR #1281 auto-merges on green.

## Arc

Continued the mining plan. The two structures/exploration mining plans are `historical` (all
slices shipped); the one **active** plan,
[`mining-hub-redesign-2026-06-15.md`](../docs/planning/mining-hub-redesign-2026-06-15.md), had one
unbuilt slice — **PR 3, grid Mine** — fully owner-DECIDED (Q-0173). Built it end-to-end.

The linear Descend/Ascend Mine action is now a **(x, y, z) grid navigator** over a
**seed-deterministic procedural world**: six movement buttons + Mine here, fog-of-war discovery,
one shared shareable seed per guild. z = the existing depth band (so `utils/mining/world.py`
balance carries over unchanged); N/S/E/W roam laterally; Up/Down change the band (light-gated).
v1 is **encounter-free** by owner decision (encounters → a deferred later session).

## Shipped (PR #1281)

- `utils/mining/grid.py` — pure seed-deterministic `cell_at` (richness + depth-weighted featured
  ore), lateral movement, loot folding, fog-of-war map render.
- migration **085** — `pos_x`/`pos_y` on `mining_player_state` + `mining_world` (per-guild seed) +
  `mining_discovered` (fog of war). Additive: no row → `(0,0)`; no seed row → `seed = guild_id`.
- `utils/db/games/mining_grid.py` — conn-aware primitives; the three writers
  (`set_position` / `mark_discovered` / `set_world_seed`) added to the RS02 boundary ratchet.
- `mining_workflow.move` / `mine_here` / `reseed_world` — one transaction each; every move marks
  discovery, `mine_here` folds the cell into the loot; `MineResult` gained an additive `cell_note`.
- `views/mining/grid_mine_view.py` (`MineGridView`) — D-pad navigator re-rendered in place;
  **replaced** the interim linear `MineView` (deleted). `!mine` opens it; `!mineworld`
  shows/reseeds the shared seed.
- Tests: pure grid, db primitives, workflow ops, the view; rewrote the two `MineView` tests onto
  the navigator. Regenerated `dashboard.json`/`site.json`/`data.js` for the new command.
- Docs: ticked PR 3 in the hub-redesign plan, updated the games folio, captured the deferred
  encounters follow-up ([idea](../docs/ideas/mining-grid-encounters-2026-06-22.md)).

## Decisions made alone (ratify if wrong)

- **Migration number 085** (not 086): next-free on `main`; PR #1279 also claims 085 but is
  review-gated and won't auto-merge, so this lands first and stays contiguous — #1279 renumbers on
  its rebase (the migration-structure test forbids gaps, so a leapfrog 086 was wrong).
- **Cell model:** NORMAL/RICH/BARREN/TREASURE with richness ×{1, 2, 0.5, 3}; rich/treasure cells
  yield their *featured* ore (a lucky strike), barren never yields zero (`max(1, …)`). Featured ore
  is depth-weighted (reuses `ore_weights_for_depth`) so "deeper = richer" needs no new table.
- **Fog of war via a `mining_discovered` row-per-cell**, read windowed (O(window)); `move` marks
  both origin and destination so looking back isn't re-fogged.
- **`!mineworld` reseed gated on `manage_guild`** (prefix command, `panel_action` classification —
  satisfies the command-surface ledger's hidden-route Rule H, like `!chop`).

## Context delta (reflection interview)

- **Needed but not pointed to:** that **`check_quality.py` is stricter than CI for isort/black** —
  it scans `tests/` while real CI `--skip tests`. A new test file's import block tripped the local
  mirror though CI would skip it; the journal/CLAUDE warning frames test-formatter reds as *false*,
  but here the mirror was simply stricter (harmless to satisfy). Worth a one-line journal note.
- **Discovered by hand:** the **command-surface ledger's static AST mirror** only pins the
  *top-level slash* surface (`EXPECTED_SLASH_SURFACE`); a new *prefix* command needs no pin, only a
  valid hidden-route classification (Rule H). And the **generated-artifact freshness tests** fail
  the *whole suite* when a command is added without re-running `export_dashboard_data.py` — the
  dashboard structural check compares `cogs`/`commands`/`env`/`settings`/`catalogue`/`synonyms` but
  **not** the `updates` feed or `functions`, so flipping a born-red card never re-stales them.
- **Pointed to but didn't need:** CodeGraph — `context_map.py` (auto-shown per file) + targeted grep
  carried the whole navigation; the symbol graph wasn't needed for this contained, well-specced slice.

## ⟲ Previous-session review (#1280 — wrong-branch guard + friction→guard reflex)

- **Did well:** institutionalized a strong meta-rule — *any workflow friction → ship the cheapest
  durable guard* — and shipped a concrete wrong-branch PreToolUse guard as its dogfood. Exactly the
  right altitude of improvement.
- **System improvement it surfaces (honest tie-in):** that reflex isn't yet applied to the friction
  *this* session hit — adding a command silently staled `dashboard.json`/`site.json`/`data.js` and
  red the whole suite until I remembered to re-export. A guard (below) is the natural next dogfood of
  the very reflex #1280 codified.

## 🛠 Friction → guard

- **Friction:** adding `!mineworld` failed 4 freshness tests because the committed generated
  artifacts weren't re-exported — a recurring footgun for *any* command/cog/setting PR.
- **Guard (proposed, owner-gated — it's a hook/settings change, Q-0106):** have the Stop hook run
  `export_dashboard_data.py` (and stage its output) when a `disbot/**` command/cog/setting source
  changed this turn, the same way it runs `check_quality`. Captured as the session idea below; not
  self-applied (executable config is owner-only).

## 💡 Session idea

- **Auto-regenerate generated artifacts in the Stop hook on a command/cog/setting source change**
  (the friction above). The per-merge `dashboard-data-refresh` workflow (Q-0167) self-heals *after*
  merge, but the freshness tests gate *before* merge, so a feature PR must remember the manual
  re-export. A Stop-hook regen-and-stage (mirroring the existing quality-check step) removes the
  footgun. Owner-gated (hook) → recorded here as a proposal, not applied.

## 📤 Run report

- **Did:** shipped the grid Mine — (x,y,z) seed-deterministic world + 6-direction navigator,
  replacing the linear Descend/Ascend. · **Outcome:** shipped (PR #1281, auto-merge on green)
- **Shipped:** #1281 — mining grid Mine (hub-redesign PR 3)
- **Run type:** `routine · dispatch` (owner-directed "continue the mining plan")
- **⚑ Owner decisions needed:** none — design was fully Q-0173-decided
- **⚑ Owner manual steps:** none (merge auto-deploys; the world defaults to `seed = guild_id`, no
  data-seed step). *Optional live check:* `!mine` to roam the grid, `!mineworld <n>` to reseed.
- **⚑ Self-initiated:** none promoted to a build — the grid Mine build was the dispatched task; two
  *ideas* captured (grid-encounters follow-up; artifact-regen Stop-hook guard), neither built.
- **↪ Next:** mining grid v2 = **depth-gated sparse encounters** (own session, owner-paced —
  [idea](../docs/ideas/mining-grid-encounters-2026-06-22.md)); otherwise the current-state ▶ Next
  action queue (Project-Moon runtime PR 1 · botsite React migration · Starboard PR 2 · …).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 at write (#1281 auto-merges on green) |
| CI-red rounds | 0 real (born-red hold is by design; full suite green locally before the completing push) |
| Repo-rule trips | 0 (isort blank-line + artifact-freshness both caught locally pre-push, not CI) |
| New ideas contributed | 2 (grid-encounters follow-up; artifact-regen Stop-hook guard) |
| Ideas groomed | 1 (encounters intake + dedup vs. `wild-encounters-activity-spawning`) |
