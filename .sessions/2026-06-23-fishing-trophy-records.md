# 2026-06-23 — Fishing trophy records (per-species biggest-caught)

> **Status:** `complete` — fishing trophy records shipped (PR #1351), full CI mirror green.

> **Run type:** `routine · dispatch`

## What I'm about to do

Scheduled dispatch fire, no work order → advance the next plan slice. Building the
**"Trophy records per species (biggest caught)"** follow-up from the fishing design
([`docs/planning/fishing-minigame-design-2026-06-22.md`](../docs/planning/fishing-minigame-design-2026-06-22.md)
§"Other ideas", line 206) — "a cheap long-tail goal layered on the existing catch-log;
personal best beats raw counts for retention."

Each catch now rolls an individual **weight**; the catch-log tracks the player's heaviest
of each species (re-introducing the `best_weight` column that #1036/migration 076 dropped
when v1 went weightless — legitimate now that this feature gives weight a purpose). The
Fishdex shows your personal-best weight per species, and a fresh record celebrates with
"🏆 New personal best!" on the catch.

Scope (additive, no money/safety seam — game state, ADR-002 applies):
- `utils/fishing/weight.py` (new, pure) — `roll_weight(species, rng)`.
- `utils/fishing/fish.py` — `Catch` gains `weight`.
- `utils/fishing/rewards.py` — `roll_catch` rolls + carries the weight.
- migration 095 — re-add `best_weight REAL NOT NULL DEFAULT 0`.
- `utils/db/games/fishing.py` — `record_catch(..., weight)` tracks GREATEST best,
  returns the prior best; `get_fishing_records()` read model.
- `services/fishing_workflow.py` — thread weight through `commit_catch`; `FishResult`
  gains `weight` + `new_personal_best`.
- `views/fishing/cast_view.py` + `menu.py` — surface weight + the trophy line.
- Tests across all layers.

## What shipped

**Fishing trophy records (per-species biggest-caught)** — PR #1351, the design's
"Other ideas" follow-up. Each catch now rolls an individual **weight**; the catch-log
tracks the player's heaviest of each species, and the Fishdex + the catch embed surface it.

- **`utils/fishing/weight.py`** (new, pure) — `roll_weight(species, rng)`: a nominal that
  grows with `size_rank` (`0.18 × rank^1.65`) × a bounded per-catch spread (0.65–1.55), so
  repeat catches differ and a lucky lunker becomes a record worth chasing. `nominal_weight`
  exposed for the curve. Seed-deterministic.
- **`utils/fishing/fish.py`** — `Catch.weight` (defaults 0.0 → old bare `Catch(species=…)`
  call sites + a 0-weight catch never set a PB).
- **`utils/fishing/rewards.py`** — `roll_catch` rolls the weight off the same rng.
- **migration 095** — re-adds `best_weight REAL NOT NULL DEFAULT 0` (additive, `IF NOT
  EXISTS`), the column 076 dropped when v1 went weightless — now that weight has a purpose.
- **`utils/db/games/fishing.py`** — `record_catch(…, weight)` keeps `best_weight` via a
  `GREATEST` upsert and returns the **prior** best (CTE), so the caller detects a new PB;
  `get_fishing_records()` read model (`best_weight > 0` filter skips legacy rows).
- **`services/fishing_workflow.py`** — `FishResult.weight` + `.new_personal_best`, threaded
  through `commit_catch` (prior-best `None` or `< weight` → PB).
- **`views/fishing/cast_view.py`** — the catch embed reports "⚖️ It weighs **X kg**" + "🏅
  **New personal best!**" on a record. **`views/fishing/menu.py`** + `cogs/fishing_cog.py` —
  the Fishdex shows "🏅 X kg" beside each caught species' tally.
- **Tests** — `test_fishing_weight.py` (new: determinism, monotonic nominal, bounded spread,
  per-catch variation); updated db/workflow/menu/cast-view tests for the weight path + PB
  flag. Full CI mirror green (12011 passed) + arch strict 0 errors.

## Findings / decisions

- **No new bugs found.** The reintroduction of `best_weight` is clean: 076's drop comment
  explicitly anticipated a future weight purpose, and 095 is `IF NOT EXISTS`-idempotent
  against either form of 075 a DB may have applied (the migration-hygiene precedent 076 set).
- Weight is **cosmetic/record-only** — it does not touch coins, the sell value (still
  `size_rank`), or any safety seam. ADR-002 (game state not restart-safe) applies, unchanged.

## 💡 Session idea

**"A big one got away" soft-fail clue + a personal-best leaderboard.** Two cheap layers on
this PR's weight seam: (1) when a *trophy* fish escapes the reel, the cast view already knows
its species — surface a teasing clue ("a *big %s* slipped the hook!") instead of a flat
"it got away", turning a failure into a bait for the next cast (the design's "Other ideas"
soft-fail item, now trivially reachable since catches carry weight). (2) A `fishtop`-style
**heaviest-catch leaderboard** off `best_weight` (the `top_fishers` pattern, new
`SUM`-less `ORDER BY MAX(best_weight)`), so trophies compete server-wide, not just personally.
Routed: both belong under the fishing design's §"Other ideas" — captured here, not yet a plan.

## ⟲ Previous-session review

The previous run (`2026-06-22-repo-navigation-cleanup`) did a careful, *restrained* job: it
pruned genuinely stale claims but verified each flagged "conflict" against source and
explicitly declined to churn append-only history or self-edit propose-first CLAUDE.md content
— exactly the discipline the working agreement asks for. What it could have done better: it
identified a real **clarity nit** (the "Open PR READY" Q-0103 bullet lacks a forward-pointer
to the Q-0133 born-red refinement ~40 lines down) but left it only as a finding, not a router
DISCUSS Q — so the fix has no durable home and will be re-discovered. **System improvement it
surfaces:** when a session finds a propose-first CLAUDE.md nit it *can't* self-edit, the
default should be to **open the router Q in the same breath** (the agreement's "propose, not
apply" path), not just note it — otherwise the observation evaporates. I did not hit that case
this run (no CLAUDE.md change), so nothing to route from my side.

## 📤 Run report

- **Run type:** `routine · dispatch`
- **Slices shipped:** 1 (fishing trophy records — a complete, shippable function: weight roll
  → DB record → workflow → both UI surfaces → tests).
- **⚑ Self-initiated:** none (this is a dispatched/next-plan-slice build straight off the S1
  fishing "Next startable" list + the design's "Other ideas" — not an invented feature).
- **⚑ Owner-decisions:** none.
- **⚑ Owner-manual-steps:** none — migration 095 auto-applies on deploy (the version-numbered
  runner); the merge auto-deploys. No seed/data step.
- **Bug-book:** no entries opened or closed this run.
