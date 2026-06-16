# Idea — round-range comparison: accept round-anchored bare-range lists

> **Status:** `ideas` — captured 2026-06-16 (Q-0089 session ender, the §7.5 round-range floor #955).
> Small/safe/decided-lane enhancement to a just-shipped builder. Owner of the area: AI / BTD6 floor.

## The gap

The §7.5 round-range cash comparison floor (`deterministic_round_range_comparison_reply`, #955)
requires a **round token before each range's first anchor** — "rounds 20-40 or **rounds** 40-60".
This conservatism is deliberate: it keeps crosspath codes like `5-0-0 ninja` from being mis-read as
a round range (the bare `5-0` would otherwise parse). But it means the very natural comma-list
phrasing where only the **first** range carries the word "rounds" —

> "do I get more money from **rounds** 1-30, 30-60 or 60-80?"

silently **defers to the model**, which then assembles the ranking itself — the exact BUG-0009
"grounded values, wrong assembly" class the floor exists to own. (Verified during #955: that phrasing
returns `None`; "rounds 1-30, rounds 30-60 or rounds 60-80" fires correctly.)

## The idea

A **round-anchored bare-range** extension to `_extract_round_ranges`: once the message contains
**≥1 explicit round-token range** (so it is unambiguously round-themed), also accept subsequent bare
`N-M` / `N to M` ranges that are **not crosspath-shaped** — i.e. reject any `N-M` that is immediately
preceded or followed by `-\d` (which would make it the middle of an `N-N-N` upgrade code). That
covers the comma-list phrasing without re-opening the crosspath false-positive the leading-token
rule closes.

## Why it's worth having

- Closes a real, common phrasing on a path whose whole purpose is to stop the model mis-ranking cash.
- Cheap + contained: one helper change + a couple of tests; no new data, no new seam.
- Bounded risk: the "≥1 explicit round-token range present" gate keeps it from firing on arbitrary
  `N-M` text, and the crosspath-adjacency reject keeps upgrade codes out.

## Disposition

Decided-lane (extends a shipped, owner-aligned feature) — a future AI/BTD6 session can build it
directly. Add a fail-against-old test for the comma-list phrasing and a crosspath-adjacency negative.
