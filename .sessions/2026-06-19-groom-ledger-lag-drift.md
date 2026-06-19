# 2026-06-19 — Groom: ledger guard distinguishes benign lag from real drift

> **Status:** `in-progress`

## Arc

Grooming pass (Q-0015 standing secondary task, owner-selected this session). Moved two related,
unbuilt, decided-lane ideas down their lifecycle by **executing** them together — both key on the
reconciliation marker, so they're one coherent change:
- `ledger-guard-benign-lag-vs-drift-2026-06-14`
- `ledger-window-scale-to-marker-2026-06-19`

## What I'm about to do

Implement marker-aware `scripts/check_current_state_ledger.py`: parse the `Last reconciliation
pass:** PR #N` marker, split missing PRs into drift (`<= N`) vs benign lag (`> N`), gate `--strict`
on drift only, and auto-size the window to the band. Mark both idea files `historical`.

_Born-red per Q-0133; flips to `complete` last._
