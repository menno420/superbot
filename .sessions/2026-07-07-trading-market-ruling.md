# 2026-07-07 — Trading-repo market ruling (Q-0250: stocks-first)

> **Status:** `complete`
> **Branch:** `claude/rebuild-plan-consolidation-c34c0b` (restarted from main after #1795) · **PR:** #1796
> **Continues:** the 2026-07-07 consolidation conversation (PRs #1791–#1795)

## What happened

Recorded **Q-0250** — the owner's answer to the trading repo's "which market first" fork:

- **Stocks-first, US large-cap tech** (his actual domain: DEGIRO, Intel/Nvidia-class); the crypto
  proving-ground suggestion is withdrawn — owner preference wins and the technical case supports
  it (mega-cap data is cheap/clean; survivorship bias is a broad-universe problem; the
  falsification ladder proves out fine on liquid large caps).
- Three binding riders: **point-in-time universe rule** (never "the stocks I hold now" — the
  selection-bias guard; his picks become watchlist inputs, not the universe); the **automated
  paper lane rides an API broker** (DEGIRO has no official API; unofficial clients are
  ToS-violating and brittle); **DEGIRO integrates read-only at the tracker** via transaction
  export — the owner's real portfolio becomes a benchmark lane beside the strategies' paper
  portfolios.
- Capture-doc fork closed (only the distant live-cap numbers remain open there).

Checks: `check_docs --strict` ✓.

## Session enders

Same conversation as the main consolidation session — enders live in
`.sessions/2026-07-07-rebuild-idea-consolidation.md`.
