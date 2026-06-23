# 2026-06-23 — Fishing trophy records (per-species biggest-caught)

> **Status:** `in-progress` — born-red session card (Q-0133). Flip to `complete` last.

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

_(filled in at close)_
