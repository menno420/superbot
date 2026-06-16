# 2026-06-16 — BTD6 "d67 dart paragon" degree-parse bug fix (BUG-0015)

> **Status:** `complete`

**Branch:** `claude/gifted-noether-37tiwr` · **Date:** 2026-06-16 · owner-reported bug (live
screenshot): "found another bug, can you fix this". · **PR #963**

## What I'm about to do

**Bug (live screenshot).** Asked "whats the damage of a **d67 dart**" / "a **d67 dart praragon**",
SuperBot answers *"A 0-6-7 Dart Paragon doesn't exist — upgrade tiers cap at 5…"*. It misreads the
shorthand **"d67" = degree 67** as an upgrade-path code "0-6-7". Paragons have **degrees 1-100**;
"d67" is the degree, not a crosspath. Bug-book class BUG-0003/0004 ("model freelances on the
unguarded general path") — confirmed two-layer root cause (routing + grounding).

## ✅ Done — PR #963

**Two-layer root cause confirmed by tracing the pipeline; fixed at four coordinated layers (the
proven BTD6-bug shape, e.g. BUG-0003/0004):**

1. **Routing** — `classify("a d67 dart praragon")` → `GENERAL_NL_ANSWER`: no keyword (`paragon`
   excluded as English), no entity (single-word tower "dart" dropped), no round/money/follow-up
   cue. The general path has **no grounding and no number guard** → the model freelanced from
   memory and misread "d67".
2. **Grounding** — even on the BTD6 path, `_render_paragon_stats` only anchors **Degree 1 + Degree
   100**; no degree-67 figure existed and nothing told the model "d67" is a degree.

Fix (the exact-degree machinery already existed — `utils/btd6/paragon_degrees`, `_paragon_main_bits`,
`btd6_stats_service.paragon_stats_at_degree` — only parse → route → ground were missing):

- **`utils/btd6/keywords.py`** — `DEGREE_CUE_RE` + `degree_in_text()` (one shared cue, the
  `ABR_CUE_RE` pattern): "d67" / "degree 67" / "deg 67"; digit-boundary guarded (a round "r67",
  version "v55", dice "5d6", temperature "67 degrees" never match), range-checked 1-100.
- **`services/ai_task_router.py`** — `_looks_like_paragon_degree`: a degree token **+** a paragon
  reference (the word "paragon", or a tower/paragon that resolves) routes `btd6.answer`. A bare
  "degree 5" / "d20 dice" with no paragon stays general.
- **`services/btd6_context_service.py`** — new Pass 3b3 `_paragon_degree_facts`: grounds the
  in-scope paragon's exact **non-linear** headline at the requested intermediate degree, explicitly
  labelled "Degree N", plus a note that a degree is NOT an upgrade-path code. D1/D100 stay the
  `_render_paragon_stats` anchors (no duplication).
- **`services/ai_instruction_service.py`** — one task-contract clause teaching the "d67"/"degree 67"
  shorthand (defense-in-depth for the production tool path; preserved every token the discipline
  test pins).
- **Bug-book BUG-0015** entry with the stays-fixed guard named.

Verified: `resolve_paragon("a d67 dart praragon" | "d67 dart")` → `apex_plasma_master`; the grounded
D67 headline is **48 dmg / 355 pierce / 0.3176s, boss ×1.75, 82,860 power** — genuinely non-linear
vs D1 (25/210/0.5) and D100 (60/430/0.2935). `check_quality --full` GREEN (10095 passed, +~30 new) ·
`check_architecture --mode strict` 0 errors · `check_docs --strict` ✓.

Tests: `tests/unit/utils/test_btd6_keywords_degree.py` (parser: recognises forms; rejects
round/version/dice/temperature/out-of-range) · `test_paragon_degree_questions_route_to_btd6_answer`
+ `test_degree_without_paragon_or_paragon_without_degree_stays_general` (router) ·
`test_paragon_degree_facts_*` (grounding: exact non-linear degree, skips D1/D100 anchors, silent
without both signals, names a directly-named paragon too).

## Context delta (what the next session should know)

- **Route miss → found by tracing.** This bug's home wasn't obvious from the orientation route: the
  symptom looked like a paragon-data gap, but the real cause was **routing** (`ai_task_router`
  dropping the question to the unguarded general path) plus **grounding coverage**
  (`_render_paragon_stats` anchoring only D1/D100). The `btd6.md` folio routes to data/provenance,
  not to "where does a natural-language BTD6 question get classified + grounded" — the answer is
  `ai_task_router.classify` (the `_looks_like_*` ladder) → `btd6_context_service.build` (the Pass
  3x legs). A pointer from the BTD6 folio to that NL pipeline would have saved the trace.
- **The unguarded general path is the recurring BUG source.** BUG-0001/0003/0004/0008 and now 0015
  all reduce to "the router didn't recognise the BTD6 question, so it hit `GENERAL_NL_ANSWER` where
  numbers are never guarded and the model freelances." The router's `_looks_like_*` ladder is the
  high-leverage place — every new community shorthand (despo, impop, r53, **d67**) needs a leg.
- **Decisions made alone:** (a) fix at grounding+routing (let the model phrase from grounded facts)
  rather than a deterministic floor reply — consistent with the existing paragon-stat grounding and
  preserves the conversational tone the screenshots show; (b) the degree leg fires only on a
  *resolvable* paragon (via `resolve_paragon`, which already does tower→paragon), so bare "d67" and
  dice "d20" never over-route; (c) deferred the Recently-shipped ledger entry to the reconciliation
  routine (Q-0124 / #962 precedent) — the bug-book is the canonical durable home.
- **Weak point / known limit:** the grounded D67 figure pins to the live dataset (the test asserts
  "48 dmg"); a future v-bump that re-sources Apex Plasma Master would need that value refreshed —
  same as the existing D1/D100 pins in `test_btd6_paragon_stats.py`.

## Session enders

**💡 Session idea (Q-0089).** *Hero per-level stat grounding — the hero sibling of BUG-0015.* Heroes
level **1-20** and players write "obyn at level 20" / "lvl 20 quincy"; the model can freelance
per-level hero stats exactly as it freelanced the paragon degree, on the same unguarded general
path. Mirror this fix for heroes: a `level_in_text` cue (reuse the degree machinery shape) + a
router leg (hero reference + level token) + a `_hero_level_facts` grounding leg over whatever
per-level hero data exists. Dedup-checked `docs/ideas/` (no hero-level / per-level-hero / shorthand
idea exists; only `grounding-completeness-claim-primitive` mentions "shorthand" in passing). Worth
an idea file if hero per-level data is actually present in the dataset (needs a check first).
Captured here, not promoted — a new idea is not a new priority.

**⟲ Previous-session review (Q-0102).** The previous session (#962, paragon **base-cost
comparison**) did its lane well — clean `_BTD6_LIST_BUILDERS` exclusivity invariant, careful
defer-ordering, a scoped handoff. What the recent §7.5 paragon arc (#946/#950/#955/#962) **missed**:
it built ever-richer paragon *comparison* tools while the most basic natural-language paragon path —
"a single paragon at degree N" — was silently broken at the **parse/route** layer (the degree
machinery existed since the wiki port, but nothing fed it from a user message). Comparison features
were layered on top of a foundation with a hole in it. **System improvement surfaced:** the 34/34
eval ratchet covers *tools*, but every live-miss bug (BUG-0001…0015) comes from **parse/route**
gaps that tool-coverage never exercises. A small **"community-shorthand corpus" eval** — run the
real shorthands (`despo`, `impop`, `r53`, `420 farm`, **`d67`**, and the next ones) through
`ai_task_router.classify` + a grounding assertion — would catch this whole class *before* users do.
Genuinely worth building; flagged here, not built this session (it's an eval-infra slice, not a
bug-fix slice).

**Doc audit (Q-0104).** `check_docs --strict` ✓ · `check_architecture --mode strict` 0 errors ·
`check_quality --full` green (10095). Bug-book **BUG-0015** added (the canonical durable home for
this fix). Recently-shipped #963 entry **deferred to the reconciliation routine** (Q-0124 — the pass
is due now at the #960 crossing and owns the ledger sweep, incl. the 11 already-unrecorded merges;
matches the #962 same-day precedent), avoiding the current-state parallel-edit hotspot. No ▶ Next
pointer change (a bug fix, not a lane advance). No new owner decision (the fix is an in-lane
engineering call). active-work claim cleared at close.

## 📤 Run report

- **Did:** root-caused + fixed the owner-reported "d67 dart paragon → 0-6-7 doesn't exist" bug
  (BUG-0015) — paragon degree shorthand parsed, routed, and grounded · **Outcome:** shipped
- **Shipped:** #963 — `DEGREE_CUE_RE`/`degree_in_text` (keywords) + `_looks_like_paragon_degree`
  (router) + `_paragon_degree_facts` Pass 3b3 (grounding) + a task-contract shorthand clause; the
  fix is deterministic, no model-loop dependency. CI mirror green (10095); arch 0; auto-merge armed
  on green (Q-0127).
- **⚑ Owner decisions needed:** `none` (an in-lane engineering call; the hero per-level extension is
  captured as a session idea, not a decision).
- **⚑ Owner manual steps:** `none` — the fix is code-only (no data file changed), so **no
  `!btd6ops seed-data` step**; the merge auto-deploys to Railway.
- **↪ Next:** unchanged — the ▶ NEXT plan-first lanes (AI §7 next workflow family, image moderation
  Q-0108, Hermes bug-triage write Q-0121) per current-state. The reconciliation routine (due at #960)
  should sweep #963 + the 11 unrecorded merges into the living ledger.
