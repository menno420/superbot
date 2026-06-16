# 2026-06-16 — BTD6 "d67 dart paragon" degree-parse bug fix

> **Status:** `in-progress`

**Branch:** `claude/gifted-noether-37tiwr` · **Date:** 2026-06-16 · owner-reported bug (live
screenshot): "found another bug, can you fix this".

## What I'm about to do

**Bug (live screenshot).** Asked "whats the damage of a **d67 dart**" / "a **d67 dart praragon**",
SuperBot answers *"A 0-6-7 Dart Paragon doesn't exist — upgrade tiers cap at 5…"*. It misreads the
shorthand **"d67" = degree 67** as an upgrade-path code "0-6-7". Paragons have **degrees 1-100**;
"d67" is the degree, not a crosspath. Bug-book class BUG-0003/0004 ("model freelances on the
unguarded general path") — confirmed two-layer root cause:

1. **Routing.** `classify("a d67 dart praragon")` → `GENERAL_NL_ANSWER`: no keyword (`paragon` is
   excluded as English), no entity (single-word tower "dart" is deliberately dropped), no
   round/money/follow-up cue. The general path has **no grounding and no number guard**, so the
   model freelances from memory and misreads "d67".
2. **Grounding.** Even on the BTD6 path, `_render_paragon_stats` only anchors **Degree 1 + Degree
   100** — no degree-67 figure exists, and nothing tells the model "d67" is a degree.

The degree machinery already exists (`utils/btd6/paragon_degrees`, `_paragon_main_bits`,
`btd6_stats_service.paragon_stats_at_degree`); the gap is parse + route + ground. Validated:
`resolve_paragon("a d67 dart praragon"|"d67 dart")` → `apex_plasma_master`; D67 = 48 dmg / 355
pierce / 0.3176s, boss ×1.75 (non-linear vs D1 25/210/0.5 and D100 60/430/0.2935).

**Fix (three coordinated layers — the proven BTD6-bug shape):**
- **keywords.py** — `DEGREE_CUE_RE` + `degree_in_text()` (shared cue, the `ABR_CUE_RE` pattern):
  recognise "d67" / "degree 67" / "deg 67", digit-boundary guarded (a round "r67"/version never
  matches), range-checked 1-100.
- **ai_task_router.py** — `_looks_like_paragon_degree`: a degree token **+** a paragon reference
  ("paragon" word, or a tower/paragon that resolves) routes `btd6.answer`. Conservative: a bare
  "degree 5" with no paragon stays general.
- **btd6_context_service.py** — new `_paragon_degree_facts` grounding pass: surface the in-scope
  paragon's exact (non-linear) headline at the requested degree, explicitly labelled "Degree N",
  plus a one-line note that a degree is NOT an upgrade-path code.
- **ai_instruction_service.py** — one clause teaching the model that players write "d67"/"degree 67"
  for a paragon degree (defense-in-depth for the production tool path).
- Regression tests at each layer + a bug-book BUG-0015 entry with a stays-fixed guard.

## ✅ Done

_(filled at close)_

## Context delta (what the next session should know)

_(filled at close)_

## Session enders

_(filled at close)_

## 📤 Run report

_(filled at close)_
