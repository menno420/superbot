# 2026-06-30 — Diagnostics + Counters completion-deepening

> **Status:** `in-progress`
<!-- born-red flow (Q-0133): `in-progress` while open; flipped to `complete` as the final close step. -->

**PR:** (opening) — diagnostics hub completeness + counters loop backoff.
**Branch:** `claude/funny-franklin-d1m4wk`
**Run type:** `routine · dispatch`

## What this run is about to do

Empty-fire dispatch → advance the standing S1 completion-first ▶ Next (clear assessed certs'
offline punch-lists, Q-0209). Two contained, offline, self-mergeable slices:

- **PR 1 — Diagnostics punch #1 (hub completeness):** wire `startup` + `findings` into the
  `!platform` hub's Validation category select (+ their `_dispatch` branches, audience-preserving)
  so the panel's own honesty caveat ("startup/findings remain typed-only") becomes a closed gap —
  these surfaces become button-reachable, not typed-only. Update the docstring + cert.
- **PR 2 — Counters punch #3 (loop backoff):** per-guild cooldown/backoff so a persistently-failing
  guild sync isn't silently retried-and-failed forever.

CI mirror green + arch strict before each self-merge.
