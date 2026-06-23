# 2026-06-23 — Fishing: the boat / deepwater venue (⛵ Set sail / Dock)

> **Status:** `complete` — born-red card (Q-0133) flipped green as the final step.
> Routine · dispatch (empty-fire schedule; promotes the next planned fishing slice → build,
> design §5 / expansion plan Phase 2). PR #1340 → auto-merges on green (Q-0123).

## Arc

Empty-fire dispatch run, no work order, no open PRs. The clean offline-testable S1 lane is the
next planned fishing slice: the **boat / deepwater venue** — the ⛵ Set sail / Dock toggle from
the sim-backed design (`docs/planning/fishing-minigame-design-2026-06-22.md` §5) and the
expansion plan's Phase 2 (`fishing-open-world-expansion-plan-2026-06-18.md`). Builds directly on
the shipped cast loop (#1298/#1299), rod ladder (#1301), bait (#1329/#1337), and energy (#1286).

## Plan (this PR)

- **Venue model** (`utils/fishing/venue.py`, pure) — `SHORE`/`DEEPWATER` + a `VenueProfile`
  holding the per-venue minigame tuning (bite band, floor, reaction window, base escape) sourced
  from the sim's §5 numbers; shore profile reuses the existing `minigame.py` constants (one source
  of truth for shore).
- **Deepwater species** — `venue` field on `FishSpecies` (default `shore`, so the existing 21 are
  unchanged — no rebalance/orphaning); a new boat-only deepwater catalog in `fish.json`,
  uncatchable from shore. `unlocked_species(level, venue)` filters by both.
- **Tougher deepwater minigame** — longer bite wait (6–12 s, 3 s floor), higher base escape (22%
  vs shore 6%), so the rod `escape_resist` knob finally matters → the boat is "viable with a good
  rod" (the sim's optimization-not-gate shape). `minigame.py` math parameterised by venue;
  generous reaction window kept (the anti-latency-unfairness principle).
- **Persistence** — `fishing_venue` table (migration 094) + CRUD; threaded through
  `roll_cast`/`begin_cast`/`CastStart`/`commit_catch`.
- **UI** — ⛵ Set sail / 🏖️ Dock toggle on the fishing menu + a venue line; cast embeds name the
  venue; fishdex grouped by venue; a `!sail` prefix toggle.
- **Tests** — venue model, venue-filtered roll, venue-aware minigame numbers, workflow venue
  persistence + cast threading.

## Shipped (PR #1340)

- **`utils/fishing/venue.py`** (new, pure) — `SHORE`/`DEEPWATER` + `VenueProfile` (per-venue bite
  band, reaction window, base escape; shore reuses the `minigame.py` constants — one source of
  truth) + `normalize`/`profile_for`/`toggle`.
- **`utils/fishing/fish.py`** — `venue` field on `FishSpecies` (default shore); `species_for_venue`,
  `venue_size_cap`, venue-aware `max_size_rank_for_level`/`unlocked_species`. **`fish.json`** — 11
  new boat-only deepwater species (1–21 scale), the original 21 unchanged.
- **`utils/fishing/minigame.py`** — `roll_bite_delay` takes `lo/hi/floor`; `is_trophy` judges by
  `species.venue`; `fight_escape_chance`/`roll_escape` take `base_escape`. **`rewards.py`** —
  `roll_catch(..., venue=)`.
- **`services/fishing_workflow.py`** — `Cast.venue` + `CastStart.venue_profile`; `roll_cast`/
  `begin_cast` read + thread the venue; `set_venue`/`toggle_venue`/`get_venue` (`VenueChange`).
- **DB** — migration 094 `fishing_venue` + `utils/db/games/fishing_venue.py` CRUD, wired in `db/__init__`.
- **`views/fishing/cast_view.py`** — the venue profile drives window/bite-band/escape; embeds name
  the venue. **`menu.py`** — ⛵ Set sail / Dock button, venue line, venue-grouped fishdex.
  **`cogs/fishing_cog.py`** — `!sail` (aliases `setsail`/`dock`) + venue in the menu/help-hook.
- **Tests** — new `test_fishing_venue.py` (16) + venue cases across fish/rewards/minigame/workflow/
  cast_view/menu; updated the existing single-venue tests to the venue-split contract.
- **Regenerated** `botsite/data/site.json`, `botsite/site/data.js`, `dashboard/data/dashboard.json`
  (command count 384 → 385 for `!sail`).

## Verification

- `python3.10 scripts/check_quality.py --full` → **11946 passed**, 47 skipped, 2 xfailed (after a
  black/ruff trailing-comma settle on the two touched pure modules). ·
  `check_architecture --mode strict` → **0 errors** (pre-existing warnings only). · 124/124 fishing
  tests green.

## Owner flag (handoff)

The literal §5 "shore caps at rank 12, move 13–21 to deepwater-only" rebalance is **NOT** done —
it would change a live, mid-progression feature (shore players could no longer catch sharks). The
additive approach (shore unchanged + a new deepwater catalog) delivers the full venue feature
reversibly; the literal shore-cap rebalance is a balance call left for the owner.

## Session enders

- **♻ Grooming (Q-0015):** advanced the fishing design plan down its lifecycle — marked §5
  boat/deepwater **✅ SHIPPED** with the as-built note + the new owner balance flag; de-staled the
  S1 sector "next startable" line (venue done → remaining: shore-cap rebalance · weather/time-of-day
  · trophy records · the Phase-2 boat-as-structure/travel layer).
- **💡 Session idea (Q-0089):** *A daily "fishing forecast" — a global, date-seeded modifier
  (e.g. "storm: rare deepwater fish biting, shorter windows" / "calm: faster bites")* that biases a
  venue for the day. It reuses the existing daily-seed pattern, gives a reason to fish *today* and a
  shared talking point, and slots cleanly onto the new `VenueProfile` seam (a per-day overlay on the
  profile numbers). Already half-captured in the design's "Other ideas" list; logged here as the
  concrete next-turn slice, not built (kept scope to the venue).
- **⟲ Previous-session review:** the #1338 bait-crafting run was clean, well-tested dispatch work and
  its process note ("never bare-black `tests/`") was genuinely useful — I hit the *adjacent* trap
  this run (a broad `black disbot/ tests/` would have churned the test tree), and that note is what
  kept me to per-file black. The one thing it could have flagged for a successor: the `roll_catch`/
  `begin_cast` mock signatures in the fishing test files are duplicated across three files, so any
  signature change (like this run's `venue=` kwarg) means editing ~9 mock lambdas by hand — a tiny
  shared `_fake_roll_catch` helper in a fishing test-conftest would remove that recurring friction.
  **System note:** captured as a candidate, not applied (test-helper refactor is its own small slice).
- **📋 Doc audit (Q-0104):** S1 sector file + design plan de-staled (above); the #1340 ledger entry
  is the next reconciliation pass's job (born-red card is the in-flight signal; recon marker still
  #1320, next at #1350). No drift spotted in the bug book or current-state hub. The new `!sail`
  command is reflected in the regenerated site/dashboard artifacts.

## 📤 Run report

- **Run type:** routine · dispatch
- **⚑ Self-initiated:** built the **boat/deepwater venue** (design §5 / expansion Phase 2) with no
  dispatch/owner ask (Q-0172) — a fully reversible, test-covered, additive S1 game feature on the
  existing fishing seams.
- **⚑ Owner-decisions:** none required to ship. One **flagged for review** (not blocking): whether to
  later apply the literal §5 shore-cap-at-12 rebalance (move ranks 13–21 to deepwater-only) — a live
  balance change, deliberately left additive here.
- **⚑ Owner-manual-steps:** none (merge auto-deploys to Railway, Q-0193; migration 094 applies on
  boot — no operator data step).
