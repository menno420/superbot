# Session — P1-3 machine-checkable contract invariants (the cross-cutting "stays fixed" layer)

> **Status:** `in-progress`

## What I'm about to do

The next ▶ startable plan slice (band-#900 decade queue slot 3, hardening roadmap §P1-3). The
2026-06-15 finding in `current-state.md` is that all four named tracks already carry *an*
invariant, so P1-3 is **"identify a specific uncovered contract, or close the track as
substantially-covered"** — not "land one per track from scratch".

This session: review all four tracks (settings · games terminal-state · AI declared-vs-consumed ·
BTD6 provenance), add CI-runnable invariants for the genuine uncovered contracts found, and close
the rest as substantially-covered with evidence in a P1-3 disposition doc.

**First gap found:** the games wager write-boundary (`test_game_wager_write_boundary.py`) guards a
**hardcoded `_WAGER_FILES` list** that only catches *deletion* staleness (`assert path.exists()`),
not *addition* — a newly-added two-party game calling `economy_service.credit`/`.debit` without
`allow_overdraft` escapes both checks (the mint window ships silently — exactly the P1-3 failure
mode). Adding a completeness guard.
