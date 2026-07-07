# 2026-07-07 — substrate-kit: adopt installs the enforcement (the forcing functions)

> **Status:** `in-progress`
> **Branch:** `claude/superbot-rebuild-final-review-nezu89` (restarted from main; prior PR #1778 merged)
> **Provenance:** owner-directed follow-up to the final-review session — "make sure that's all correctly done."

## Why

The Phase-2.5 re-run showed the memory kit's docs get read but not written-back. Root cause the
owner surfaced: this repo's memory discipline isn't voluntary — it's forced by (1) an end-of-session
**nag hook** and (2) a **CI locked door** that won't let a session merge without its journal. The
kit shipped the *notebook* but only *stages* (never turns on) those forcing functions, and the kit's
`check --strict` even treats a **missing** session log as advisory-not-failure — so the door doesn't
actually lock. This session closes that.

## What I'm about to do

1. Give the kit a real session-gate: `check --require-session-log` makes a *missing* log a hard
   failure (the door).
2. Make `adopt --wire-enforcement` lay down a **live** (uncommented) CI workflow that runs the gate
   + the live nag hook (composes with the bootstrap.py vendoring shipped in #1778).
3. Regenerate `dist/bootstrap.py`; add tests.
4. **Prove it end-to-end** on a scratch repo: adopt with enforcement → a session that skips the
   journal → run the gate as CI would (RED) → add the journal (GREEN). Honest note: the nag hook's
   behavioral effect needs a live CLI session; the *door* I prove directly.
5. Update the G2 / final-review writeups honestly.

*(Close-out written at session end; this card holds the merge red until then — Q-0133.)*
