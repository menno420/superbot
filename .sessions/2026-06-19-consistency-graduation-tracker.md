# 2026-06-19 — Consistency-linter graduation tracker

> **Status:** `in-progress`

## What I'm about to do

Routine dispatch (empty fire → next plan slice). Build the **per-rule graduation tracker** into
`scripts/check_consistency.py` — the #1060 session idea + the documented "graduation prep" next step on
the consistency-linter lane. Each `Rule` gains a real `severity` (graduating = flip to `error`, enforced
by `--mode strict`) + a `graduation_blocker`; a `--graduation` report makes "why is this still warn-only?"
a one-hop answer. Then de-stale the plan doc + current-state and add the 4 lagging ledger entries on sight.

(Full close-out written here as the deliberate final step; flip to `complete` last.)
