# Session: idea capture — dispatch resolution (--json + Hermes wiring)

> **Status:** `complete`

**Branch:** `claude/ecstatic-euler-bslyvd` · **PR:** (this) · **Date:** 2026-06-14 · **Type:** docs-only idea capture

## What this is
A small end-of-night capture addendum to the sector-tooling session (#882), owner-invited ("any good
ideas you have like what you just said just document it"). Single-commit docs change — card opened
`complete` (no partial-merge window to protect).

### Captured
1. **`docs/ideas/dispatch-resolution-json-hermes-2026-06-14.md`** — the genuinely-useful next step I
   described in chat: give `dispatch_menu.py` a **`--json`** mode and wire it into the Hermes
   `superbot-dispatch` skill so *"dispatch SX"* resolves to a concrete work order **and** routes by the
   resolved executor (Claude-in-repo / Hermes-VPS / maintainer). The read-side of **Q-0137 Thread 1**;
   `--json` half is a safe quick-win, the Hermes half is gated on the owner's Thread-1 decision.
   Indexed in `docs/ideas/README.md`.
2. **Journal candidate rule** (`.session-journal.md` § Reading & docs): *ship a doc convention's checker
   in the same PR that introduces it* — earned this session (the #880 ▶-in-prose drift that #882
   caught). The specific form of "dogfood what you build."

## Context
Owner is offline tonight and will check whether Hermes actually dispatched + the results in the morning.
No code; no `disbot/`. The dispatch tooling shipped this session (#882) is what a Hermes dispatch would
now resolve against. Q-0107 reconciliation stays the routine's job (next at #900).
