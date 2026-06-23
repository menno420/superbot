# 2026-06-23 — Fishing: daily weather forecast (slice 2)

> **Status:** `in-progress` — born-red card (Q-0133); flips to `complete` as the final step.
> Routine · dispatch (empty-fire schedule, **slice 2** of this run — after #1340 merged).
> Promotes this run's own Q-0089 session idea → build (Q-0172). PR auto-merges on green (Q-0123).

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
