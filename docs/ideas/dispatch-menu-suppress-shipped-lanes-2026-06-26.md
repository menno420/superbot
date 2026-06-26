# Idea — let `dispatch_menu.py` suppress already-shipped lanes at the dispatch pick

> **Status:** `ideas` — captured 2026-06-26 (dispatch run). Promotes the "left open / option (b)"
> note from the [#1477 session log](../../.sessions/2026-06-26-sessionclose-freshness-wiring.md)
> into a tracked idea so it doesn't stay buried as a one-line aside.

## The gap
`scripts/check_sector_next_freshness.py` (#1476/#1477) catches a per-sector `▶ Next` in
`docs/current-state/S*.md` that links a **shipped (`historical`) plan** — but only at session
close. The *dispatch pick* itself (`scripts/dispatch_menu.py`, read from `docs/roadmap.md` § By
sector) has **no such guard**: a roadmap `Now`/`Next` item whose linked plan already shipped is
still offered as the startable lane. This run nearly made exactly that mis-step (S3's ▶ Next had
linked a shipped plan before #1476 fixed it). Catching it at *pick time* (what Hermes / a routine
reads to choose work) is strictly earlier than catching it at *close time*.

## Why it's not a trivial port of the freshness checker
The current-state `▶ Next` sections link a single live plan, so status-reading is unambiguous.
Roadmap `Now`/`Next` bullets routinely link **multiple** plans in one bullet — some `historical`
(cited as shipped *context*), some live (the actual next work). Naive "suppress if any linked plan
is historical" would over-suppress live lanes; "offer if any is live" would under-suppress. So this
needs a **convention** first.

## Proposed convention (the prerequisite)
Mark the *operative* plan link of a roadmap `Now`/`Next` item with the existing `▶` glyph the menu
already keys on — i.e. a `Now:` bullet tags its live plan link with a leading `▶` and any shipped
plan it cites for context carries no `▶`.
`dispatch_menu.py` then reads the status of only the `▶`-tagged plan link and **suppresses /
down-ranks** a lane whose operative plan is `historical`, surfacing the next ▶ startable instead.
`check_sector_map.py` can assert the convention (each `Now`/`Next` with a plan link has exactly one
`▶`-tagged operative link).

## Build sketch (one offline, self-mergeable PR once the convention lands)
1. Define the `▶ [operative-plan]` convention in `docs/repo-sector-map.md` § dispatch targets.
2. `dispatch_menu.py`: extract the operative plan link per `Now`/`Next`, read its status (reuse the
   `plan_status` helper shape from `check_sector_next_freshness.py`), suppress/flag `historical`.
3. `check_sector_map.py`: assert the convention; tests in `tests/unit/scripts/`.

Reversible (read-only reporter + a docs convention). Pairs with the session-close freshness guard:
pick-time + close-time double coverage of the same drift class.
