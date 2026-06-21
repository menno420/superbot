# 2026-06-21 — Creature collector leaderboard provider (central hub integration)

> **Status:** `complete` — second slice of this dispatch run. Registers a
> `CreaturesProvider` in `services/rank_providers.py` so the creature game joins the
> unified `!leaderboard` / `!rank` hub (the documented "new category = register a
> provider" pattern). Additive; no migration; reuses the existing `top_collectors` read
> → self-merge on green.

> **Run type:** `routine · dispatch`

## Arc

Same dispatch run as `!temproles` (#1242, merged). After shipping slice 1, took the ▶ Next
startable (a) from current-state: *"the creature-game … leaderboards slice (reuse `game_xp`,
additive)."* The creature game (#1208/#1213/#1230) had a standalone `!dextop` top-collectors
command but was **absent from the central `!leaderboard` hub** — every other game
(xp/coins/mining/gamexp/crafting/deathmatch/rps/counting) is a registered `RankProvider`.

## What shipped

- **`CreaturesProvider`** in `services/rank_providers.py` — `top` + `member_rank` over the
  existing catalog-scoped `db.top_collectors(guild.id, creature_names())` read (caught count +
  species count). Renders `"<n> caught (<m> species)"`.
- Registered in `_PROVIDERS` (after `MiningProvider`) + exported in `__all__`. The registry is
  the **single** wiring point: the `!leaderboard` dropdown (`_select_options` iterates
  `provider_names()`), `!leaderboard creatures`, and `!rank creatures` all pick it up with no
  cog edit — exactly the design's "add a provider, not edit either cog" contract.
- Category aliases `creature` / `creaturelb` → `creatures`.
- Tests (5 new): registry membership, top rendering, 10-cap, member_rank on/off board, alias
  resolution. Updated the registry-shape pin to include `creatures`.

## Verification

- `check_quality.py --full` (CI mirror) → **GREEN — 11325 passed, 47 skipped**, mypy clean,
  formatters/consistency pass.
- `check_architecture --mode strict` → 0 errors.
- No command-count artifact drift — this adds a *category*, not a command (`!dextop` already
  existed; `!leaderboard creatures` is an arg to the existing command).
- Not live-interaction-tested in Discord (no click harness in-env).

## Context delta

- **Needed but not pointed to:** nothing new — the provider registry (PR G) was built for
  exactly this ("new category = register a provider").
- **Decision made alone:** ranked by **creatures caught** (the collection metric `top_collectors`
  already serves + the `!dextop` precedent) rather than `GAME_CREATURE` xp. The handoff said
  "reuse `game_xp`," but the catch-count board is the more player-meaningful creature metric and
  distinct from the existing xp-based `GameXpProvider`/`CraftingProvider`; the read already
  exists, so it's the cleaner additive slice. A `game_xp`-based creature board could still be
  added later if wanted.

## 💡 Session idea (Q-0089)

**Fold the standalone `!dextop` into the unified hub as a thin alias** — now that a
`CreaturesProvider` exists, `!dextop` could become a legacy alias that opens `!leaderboard
creatures` (the same `legacy_duplicate` alias-classification the other per-game shortcuts carry:
`!minelb`, `!rpslb`, …), collapsing two code paths to one render. Small, but it removes a
divergent second formatting of the same data (the cog's bespoke medal embed vs the registry's
`RankEntry` rows). Dedup-checked: the alias-classification convention already exists; this just
extends it to the creature game. Worth a follow-on slice, not done here to keep this PR a clean
pure-add.

## ⟲ Previous-session review (Q-0102)

**Reviewed: this run's slice 1 (`!temproles`, #1242).** *Did well:* a tight, fully-tested
loose-end pickup that merged clean on the first green. *What it could have done better — and the
lesson this slice applied:* slice 1 hit a predictable round of generated-artifact drift
(command-count 313→314) only *after* the full-mirror run, costing a regen round. The general
pattern — **adding a command always drifts the command-count artifacts** — is now well-documented
(BUG-0018/0022) but there's no *pre-flight* reminder. **System improvement:** a one-line check in
the `/pre-pr` skill (or the Stop hook) that, when the diff adds an `@commands.command(` /
`@app_commands.command(`, prints "↳ new command — run `scripts/export_dashboard_data.py` before
pushing" would turn a CI-red round into a zero-cost reminder. Slice 2 avoided the trap precisely
because it adds a *category*, not a command — but the next command-adding session will hit it
again. Captured as a soft tooling improvement (not a binding-rule proposal).

## 📤 Run report

- **Did:** registered `CreaturesProvider` in the rank-provider registry, integrating the creature
  game into the unified `!leaderboard` / `!rank` hub (auto-wired dropdown + `!leaderboard
  creatures` + `!rank creatures`) · **Outcome:** shipped (routine dispatch, self-merge on green)
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions recorded:** none
- **⚑ Owner manual steps:** none — merge auto-deploys; no migration (reads existing
  `creature_collection_log`).
- **⚑ Self-initiated:** the whole slice — a plan-queued ▶ startable (current-state ▶ Next (a)),
  not a dispatched work order (empty scheduled fire advances the plan). Contained, reversible,
  additive, test-covered.
- **↪ Next:** the session idea above (fold `!dextop` into the hub as a legacy alias); else a fresh
  ▶ ungated startable — the **botsite React-SPA migration**
  ([plan](../docs/planning/botsite-react-spa-migration-plan-2026-06-20.md)) or a substantial
  `needs-hermes-review` lane (consistency-linter AI-nav PR 1 · procedures→skills Batch 2).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs this session (this slice) | 1 (#1244, routine dispatch, self-merge on green) |
| Migrations added | 0 (reads existing `creature_collection_log`) |
| New tests | 5 (top render · 10-cap · member_rank on/off · alias) + 1 registry-pin update |
| CI-red rounds | 0 local (born-red gate only, by design) |
| Repo-rule trips | 0 (arch 0 errors) |
| New ideas contributed | 1 (fold `!dextop` into the hub as a legacy alias) |
