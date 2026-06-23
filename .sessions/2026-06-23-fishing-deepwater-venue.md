# 2026-06-23 — Fishing: the boat / deepwater venue (⛵ Set sail / Dock)

> **Status:** `in-progress` — born-red card (Q-0133); flips to `complete` as the final step.
> Routine · dispatch (empty-fire schedule; promotes the next planned fishing slice → build,
> design §5 / expansion plan Phase 2). PR auto-merges on green (Q-0123).

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

## Owner flag (handoff)

The literal §5 "shore caps at rank 12, move 13–21 to deepwater-only" rebalance is **NOT** done —
it would change a live, mid-progression feature (shore players could no longer catch sharks). The
additive approach (shore unchanged + a new deepwater catalog) delivers the full venue feature
reversibly; the literal shore-cap rebalance is a balance call left for the owner.
