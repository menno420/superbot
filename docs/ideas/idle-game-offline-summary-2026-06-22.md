# Idea — "while you were away" offline-progress summary for idle games

> **Status:** `historical` — **BUILT 2026-06-22** (PR #1331): `utils/idle_summary.py`
> (`format_duration` + `summarize_idle_gain`) shipped + wired into the farm panel as its
> first consumer. Kept for provenance. The reuse-by-a-second-idle-system step is the live
> remainder (fold the mining/fishing energy hubs onto the same helper on the rule of three).

## The idea

The chicken farm (shipped this session) is the bot's first **idle** game: progress
accrues while the player is away. The most satisfying moment of any idle game is the
**return moment** — "while you were away, your hens laid **17 eggs** (worth 34 🪙)".
Right now the farm panel just shows the current coop fill; it never *narrates* the gap
since the last visit.

Propose a small shared helper — `utils/idle_summary.py` — that, given a settled-vs-stored
delta (eggs gained since `*_updated_at`, capped reached y/n, time elapsed), renders a one
-line "while you were away" blurb. The farm panel shows it on open; future idle systems
(a second idle game, the mining-energy regen, the fishing-energy regen) reuse the same
helper so the return-moment copy is consistent bot-wide.

## Why it's worth having

- It's the cheap, high-impact polish that makes idle games *feel* idle — the reason
  the genre is sticky. The accrual math already exists (`settle()`); this only renders
  the delta.
- It's a genuine **rule-of-three candidate**: farm + the two energy bars all have a
  "stored value + timestamp settled forward" shape, so a shared summary helper is the
  natural place the third occurrence justifies extracting (the same trigger the farm's
  `settle()` copy already flags).

## Rough shape

- `utils/idle_summary.py` (pure): `summarize(before, after, elapsed_s, *, unit, cap_hit)`
  → a short string. No DB, no Discord — unit-testable like the rest of `utils/farm`.
- Farm panel passes the pre-settle vs post-settle egg counts when it opens.
- Later: fold the same blurb into the mining/fishing hubs.

Lifecycle: `captured`. Next step = a small plan (it's a clean single-PR slice) or
execute directly in a future grooming pass since it's small/safe/reversible.
