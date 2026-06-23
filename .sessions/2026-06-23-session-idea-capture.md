# 2026-06-23 — Promote loose session ideas into the docs/ideas backlog

> **Status:** `complete` — born-red card (Q-0133) flipped green as the final step.
> Owner-directed (chat: "make sure all ideas etc are properly documented so nothing important from
> this session is lost"). Docs-only. PR #1362 auto-merges on green (Q-0123).

## Arc

Session-close documentation audit for the 2026-06-23 visual-engine / AI-setup arc (#1349 card
engine · #1352 positioning · #1355 + #1357 `/setup-describe` · #1361 create-count guard). Audit
findings:

- **Shipped work is durably captured:** the Dank Memer visual research → the card-engine vision doc;
  the 15-bot competitive research → the positioning north-star doc + the competitive-positioning
  session log's "Research provenance" section; every feature → its `.sessions/` log, all merged.
- **#1361 is still open (auto-merging on green)** — it carries the create-count guard, the #1351
  ledger drift fix, and its session log; nothing lost, lands on merge. (So the #1351 "real drift" the
  SessionStart checker flags on main is already fixed in the pending PR — NOT re-fixed here.)
- **Gap closed by this PR:** three forward-ideas (Q-0089) lived only in `.sessions/` logs, invisible
  to anyone browsing the `docs/ideas/` conveyor. Promoted them into the backlog.

## Shipped (this PR)

- `docs/ideas/session-followups-visual-ai-setup-2026-06-23.md` — the three open ideas with
  provenance: (1) golden-image card-engine snapshot tests, (2) a user-visible cosmetic-only
  monetization pledge surface, (3) a per-kind breakdown in the #1361 create-count guard.
- `docs/ideas/README.md` index entry.

## Status

In progress — born-red. Close-out written as the final step before flipping to `complete`.
