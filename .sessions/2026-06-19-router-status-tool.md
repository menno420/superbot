# 2026-06-19 — router_status.py: a question-router digest tool

> **Status:** `in-progress`

## Arc

Continuation grooming-ender after the website-split planning chain merged (#1100 plan · #1102 Q-0179).
Executes the idea I captured in #1102's card (Q-0089): a small stdlib tool that digests the
6,500-line / 184-block maintainer question router — the recurring per-session friction of finding the
next free `Q-NNNN` and scanning for what's still OPEN (hit by hand twice this session).

## What I'm about to do

- Add `scripts/router_status.py` (pure stdlib, read-only, Q-0105 disposable) + a unit test:
  reports the next free Q-number (exact) + the OPEN owner-decision queue vs DECIDED, with an honest
  UNCLASSIFIED bucket. Flags: `--next` · `--open` · `--unclassified` · `--json`.
- Verify its output against the live router; standing enders; flip to complete last.
