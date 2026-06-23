# 2026-06-23 — Fishing: daily weather forecast (slice 2)

> **Status:** `complete` — born-red card (Q-0133) flipped green as the final step.
> Routine · dispatch (empty-fire schedule, **slice 2** of this run — after #1340 merged).
> Promotes this run's own Q-0089 session idea → build (Q-0172). PR #1341 auto-merges on green (Q-0123).

## Arc

Slice 1 (#1340, merged) shipped the boat/deepwater venue + the `VenueProfile` seam. Slice 2 builds
directly on it: a **daily, date-seeded global weather forecast** that biases fishing for the day —
this run's own logged session idea (the fishing design's "Other ideas" §"weather/time-of-day").
Same offline-testable S1 lane, same fresh mental context, zero conflict (main is clean post-merge).

## Plan (this PR)

- **`utils/fishing/weather.py`** (new, pure) — a `Weather` dataclass (bite-speed × rarity multipliers
  + flavour) + a small weighted `CONDITIONS` table (clear most common; storm rare); deterministic
  `weather_for_date(date)` (sha256 of the ISO date → weighted pick, so it's the **same for everyone
  on the same day** — a shared talking point) + `current_weather()`.
- **`services/fishing_workflow.py`** — `begin_cast` compounds the day's weather onto the already-
  threaded `effective_bite_speed` / `effective_pull`; `CastStart.weather` carries it for the embed.
  A `get_forecast()` read for the command/menu.
- **UI** — the cast embed + menu show today's forecast; a `!forecast` command.
- **Tests** — determinism (same date → same weather), weighting sanity, the begin_cast compounding,
  the forecast surface.

No new DB / migration (weather is derived from the date, not stored — ADR-001/002 friendly).

## Shipped (PR #1341)

- **`utils/fishing/weather.py`** (new, pure) — `Weather` (bite-speed × rarity multipliers + flavour +
  weight) + a 5-condition `CONDITIONS` table (clear 38 / rain 22 / calm 18 / fog 14 / storm 8);
  deterministic `weather_for_date(date)` (sha256 of the ISO date → weighted pick — stable across
  processes, *not* Python's salted `hash`), `current_weather(now=)` (injectable clock), `effect_text`.
- **`services/fishing_workflow.py`** — `begin_cast` compounds the day's weather onto
  `effective_pull` / `effective_bite_speed` (rod × bait × **weather**); `CastStart.weather` carries
  it; `get_forecast()` read.
- **UI** — the cast embed shows a forecast field when weather is non-neutral (clear stays silent);
  the fishing menu shows a "Today's forecast" field; new `!forecast` (aliases `fishforecast`,
  `fishingweather`).
- **Tests** — new `test_fishing_weather.py` (10: determinism, full-coverage over a 3-yr horizon,
  weight distribution, neutral-clear, storm risk/reward, effect-text) + workflow weather-compounding
  + `get_forecast` + a menu forecast-field test; pinned neutral weather in the exact-value
  `begin_cast` knob tests so they stay deterministic regardless of run date.
- **Regenerated** site/dashboard artifacts (command 385 → 386 for `!forecast`).

## Verification

- `python3.10 scripts/check_quality.py --full` → **11959 passed**, 47 skipped, 2 xfailed. ·
  `check_architecture --mode strict` → **0 errors**. · Distribution over 5 yrs tracks the weights
  (clear ≫ rain ≫ storm; storm < 15%).

## Session enders

- **♻ Grooming (Q-0015):** marked the fishing design's "weather/time-of-day" Other-idea **✅ SHIPPED**
  with the as-built note; de-staled the S1 sector "next startable" line (weather done → remaining:
  the owner shore-cap rebalance · trophy records per species · the Phase-2 boat-as-structure/travel
  layer).
- **💡 Session idea (Q-0089):** *A "this week's fishing event" — a longer (multi-day) weather streak or
  a weekend-only rare-species window, layered on the same date-seed.* The daily forecast gives a
  reason to fish *today*; a weekly cadence (e.g. "Migration weekend: marlin running") would give a
  reason to come back *this week* and a softer, scheduled goal — reusing the `weather.py` date-seed
  with a week-bucketed seed. Small, contained, on the new seam. Logged, not built (kept scope).
- **⟲ Previous-session review:** slice 1 (#1340, this same run) was a clean, complete vertical feature,
  but it left a real friction this slice hit immediately — the fishing test files duplicate the
  `roll_catch`/`begin_cast` mock signatures across three files, so adding the `weather` knob meant
  pinning `current_weather` in ~9 `begin_cast` test blocks by hand (and my first scripted insert broke
  single-line `with` statements). The slice-1 review *predicted* exactly this (a shared
  `_fake_roll_catch`/fishing test-conftest helper would remove it). **System note:** that test-helper
  consolidation is now a genuinely earned, twice-confirmed small slice — a good turn-key pick for a
  future dispatch run (captured, not built; CLAUDE.md/test-infra is its own scope).
- **📋 Doc audit (Q-0104):** S1 sector file + design plan de-staled (above); the #1341 ledger entry is
  the next reconciliation pass's job (recon marker #1320, next at #1350; #1340 + #1341 are benign
  post-marker lag). The new `!forecast` command is in the regenerated artifacts. No drift spotted in
  the bug book or current-state hub.

## 📤 Run report

- **Run type:** routine · dispatch
- **⚑ Self-initiated:** built the **daily weather forecast** (this run's own Q-0089 session idea) with
  no dispatch/owner ask (Q-0172) — a fully reversible, test-covered, no-DB additive S1 game feature on
  the venue seam. (Slice 2 of the run; slice 1 = the deepwater venue #1340, merged.)
- **⚑ Owner-decisions:** none.
- **⚑ Owner-manual-steps:** none (merge auto-deploys to Railway, Q-0193; no migration / no data step).
