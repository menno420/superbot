# 2026-06-27 — Fishing acquisition depth: fish→rod craft + lucky double catch

> **Status:** `complete`

**Run type:** routine · dispatch

## What this run did

Empty-fire dispatch (no work order). Executed the **two named successors** the previous fishing run
(#1508, fish→charm craft) handed off on the S1 ▶ Next line — both `[offline]`, pure, sim-pinnable.
Two coherent slices on one PR (#1515), both deepening fishing acquisition (Q-0209 completion-first).

**Slice 1 — fish→rod craft path.** The rod ladder was coins-only (`buy_rod`). Added a non-coin earn
path, **mirroring `craft_charm`/`craft_bait` exactly**:
- `utils/fishing/rods.py`: `RodRecipe` + `ROD_RECIPES` (keyed by the tier crafted into: 10/16/26/40
  fish, size-caps 6/12/18/21) + `rod_recipe`/`rod_recipe_text`. Pure; monotonic; numbers pinned in
  `docs/planning/fishing-rod-craft-numbers-2026-06-27.md`.
- `services/fishing_workflow.py`: `craft_rod` — inventory-only conversion (no coins/audit), debits
  eligible fish (smallest-first, the shared `_plan_fish_spend`) and raises the rod tier by one in one
  `db.transaction()`; like `buy_rod` it crafts the *next* tier from the one owned.
- `cogs/fishing_cog.py`: `!craftrod` (alias `rodcraft`).
- `views/fishing/rod_shop.py`: a **🎣 Craft from fish** button beside ⬆️ Upgrade + the craft cost in
  the embed; the shared re-render renamed `_refresh`→`_rerender` (the discord.py `View._refresh`
  collision guard `test_no_view_shadows_view_refresh`).

**Slice 2 — the fish-loot drop (a 🍀 lucky double catch).** The other named successor:
- `utils/fishing/rewards.py`: `BONUS_CATCH_CHANCE` (0.10) + pure `roll_bonus_catch(rng)`.
- `services/fishing_workflow.py`: `commit_catch` rolls it at commit time (only a landed catch can
  double) → the inventory grant is `2 if bonus else 1`; new `FishResult.bonus_catch`. **Byte-identical
  when it doesn't fire**, and **never a second dex/trophy row** (`record_catch` runs once). `rng`
  injectable for test determinism. Numbers in `docs/planning/fishing-bonus-catch-numbers-2026-06-27.md`.
- `views/fishing/cast_view.py`: surfaces "🍀 **Lucky double catch!**" on the catch result.

The acquisition loops now all close on the same `_plan_fish_spend` planner:
`!fish (→ 🍀 double) → !craftbait / !craftcharm / !craftrod → fish better`.

## Verification
- New tests: **27** — `test_fishing_rods.py` (+3 craft shelf), `test_fishing_workflow_rod.py` (+6),
  `test_fishing_rod_shop.py` (new, +3), `test_fishing_rewards.py` (+3 bonus roll),
  `test_fishing_workflow.py` (+2 commit-catch bonus grant), `test_fishing_cast_view.py` (+1 bonus line).
- `python3.10 scripts/check_quality.py --full` GREEN (12914 passed; isort autofixed on
  `fishing_workflow.py`); `check_architecture --mode strict` 0 errors; mypy clean; `check_docs` +
  `check_consistency` ✓.
- Regenerated the dashboard artifacts (`+1` command → 457) so the freshness guards stay green.

## 💡 Session idea (Q-0089)
*A `!fishstats` / fishing-progress card* surfacing the three acquisition tracks in one place — rod tier
(+ next craft cost), charm set, and a lifetime "lucky double catches" tally. Now that there are three
parallel earn paths (rod/charm/bait craft) plus the bonus drop, a player has no single view of "where
am I on each track / what's my next craftable". Reuses the existing `get_rod` / inventory / catch-log
reads; pure render. Genuinely surfaced by this run (three tracks now exist where #1504 had none), not
filler.

## ⟲ Previous-session review (Q-0102)
The previous run (#1508, fish→charm craft) did its best work in the **handoff**: its ▶ Next named *both*
successors precisely (fish-loot drop *and* rod-ladder craft), and its Q-0102 note proposed naming the
**"mirror this" seam** inline on an `[offline]` ▶ Next item to cut orient cost. That paid off directly —
I knew within one read that `craft_rod` should mirror `craft_charm`, and the bonus drop should reuse the
`commit_catch` grant seam, *because #1508 spelled both out*. **I acted on its proposed improvement** in
this run's handoff below: the S1 ▶ Next successor now names its mirror seam (`commit_catch` grant /
`craft_*`). **One thing #1508 could have done better:** it left *two* successors on one ▶ Next line
without sequencing them, which risked the next run doing one and re-handing-off the other (more PR
overhead); this run instead shipped both in one PR. **System improvement surfaced:** when a handoff
names N independent offline successors that share a seam, the next run should batch them into one PR
rather than one-per-run — captured here; worth a line in the dispatch handoff convention ("co-located
successors → one PR").

## Doc audit (Q-0104)
Durable homes: the features live in code (`rods.py`/`rewards.py`/`fishing_workflow.py`/`fishing_cog.py`/
`rod_shop.py`/`cast_view.py`); balance rationale in the two new `docs/planning/fishing-*-numbers-2026-06-27.md`
docs (both linked from S1-bot.md — no orphans, the `test_repo_has_no_doc_orphans` gate confirmed); the
S1 ▶ Next line de-staled to mark both successors shipped and point at the next one with its mirror seam
named. `check_current_state_ledger --strict` lag for the newest merges is benign newest-merge lag —
recorded by the docs-reconciliation routine at the next pass (#1530), not a manual dispatch's lane
(Q-0124). Claim file deleted at close. No bug-book entry (no bug fixed/found).

## 📤 Run report
- **Did:** two fishing acquisition-depth slices on PR #1515 — fish→rod craft (`!craftrod` + rod-shop
  button) and the 🍀 lucky-double-catch fish-loot drop — both the previous run's named successors;
  27 tests + two sim-pinned numbers docs; regenerated the dashboard. Born-red → complete; auto-merge
  armed (merges on green Code Quality).
- **Next (handoff):** S1 ▶ Next — extend the same caught-fish craft pattern further (a **recipe
  browser** for the craft shelves, or a **rare dedicated craft material** drop distinct from the double
  fish). **Mirror seam:** a material drop reuses the `commit_catch` grant seam (an extra delta on a rare
  roll, like `bonus_catch`); a browser mirrors the existing `!gear`/recipe-list rendering. Both
  `[offline]`, pure, sim-pinnable.
- **Run type:** routine · dispatch
- ⚑ **Self-initiated:** none (both slices are the previous run's flagged S1 `[offline]` successors, not
  unprompted promotions).
- ⚑ **Owner-decisions:** none.
- ⚑ **Owner-manual-steps:** none (code + data only; live on the auto-deploy of the merge — no seed
  step, no migration).
