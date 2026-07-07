# 2026-07-07 — Rebuild gate-runners: kit tail ① + Phase-2.5 A/B + check_amendments (canonical-plan §5 steps 1–3)

> **Status:** `in-progress`
> **Branch:** `claude/superbot-rebuild-phase-2.5-qk07s7` (restarted from main after #1770 merged)
> **Owner ask (in-chat, 2026-07-07):** "tell me everything I need to know in plain language, and in the meantime you can do items 1-3"

## What I'm about to do

Execute the canonical plan's start-sequence steps 1–3 (`rebuild-canonical-plan-2026-07-06.md` §5):
1. **Kit tail ①** (Q-0223): make `JsonStateBackend.transaction` re-entrant + wrap
   `apply_review_verdict`'s multi-write paths atomically; rebuild `dist/bootstrap.py`; kit tests green.
2. **Run Phase-2.5** (gate G2) per companion D: seed a throwaway toy repo, 4 fixed tasks × ON/OFF
   arms as same-model sub-agent sessions, extract the 3 measures, independent judge pass, ship
   `phase-2.5-cold-start-report-2026-07-07.md` with an explicit verdict against the F-5 pass bar
   (owner accepts the verdict at G1 — the run is agents', the acceptance is his).
3. **`tools/check_amendments.py`**: the registry's named enforcer (next-free-number, append-only,
   no refuted-name reuse, spec_ref resolution) + unit tests + an advisory CI step.
Plus a **plain-language owner briefing** doc mirroring the in-chat explanation.

## Work done

_(to be filled at close)_
