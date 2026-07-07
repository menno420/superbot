# 2026-07-07 — Rebuild gate-runners: kit tail ① + Phase-2.5 A/B + check_amendments (canonical-plan §5 steps 1–3)

> **Status:** `complete`
> **Branch:** `claude/superbot-rebuild-phase-2.5-qk07s7` (restarted from main after #1770) · **PR:** #1775
> **Owner ask (in-chat):** "tell me everything I need to know in plain language, and in the meantime you can do items 1-3"

## What happened

Executed the canonical plan's start-sequence steps 1–3 plus the plain-language owner briefing:

1. **Kit tail ① (Q-0223) shipped:** `JsonStateBackend.transaction` is now re-entrant (per-level
   snapshot/rollback, single outermost flush) and `apply_review_verdict`'s fail/confirm paths are
   each one atomic transaction. 5 new tests; `dist/bootstrap.py` regenerated; **427/427 kit tests
   green** under python3.10.
2. **Phase-2.5 cold-start A/B RUN (gate G2)** per companion D: seeded a 200-line `spendlog` toy
   CLI; 4 tasks × ON/OFF arms = **8 paired same-model sessions** + scripted ground truth (all 8
   completed their tasks) + M1 transcript metrics + an **independent Opus judge**. **Verdict: FAIL
   against the F-5 bar, as tested** — `adopt` ships the kit *inert* (unrendered `${...}` templates,
   hooks pointing outside the target), so ON paid an orientation cost in 3/4 pairs (up to 2.1×)
   with zero measured benefit; no ON session used the decisions ledger or wrote a session log.
   Honest null/negative result recorded with the fix named: **adopt must render what it knows**
   (project name, verify command, loud UNRENDERED banners) + one re-run pair. Report:
   `docs/planning/phase-2.5-cold-start-report-2026-07-07.md`; canonical G2 row + §5 steps updated;
   owner accepts the ruling at G1.
3. **`tools/check_amendments.py` built (Gate-V P-9):** the registry's named enforcer (per-family
   contiguous next-free IDs, refuted-name-never-reused, status discipline, in-spec refs resolve in
   the spec_corpus) + 9 unit tests + an **advisory CI step verified green in a live CI run**.

Plus: **`rebuild-owner-briefing-2026-07-07.md`** (the plain-language companion, delivered in-chat
and committed; homed in the planning README after a check_docs orphan catch in CI), and the stale
`claude-jolly-johnson-3s6zq5` claim file removed (its PR #1772 merged; flagged by
check_stale_claims in CI — fix-on-sight).

**Bugs-first (found by the pre-flip full CI mirror):** `scripts/context_map.py`'s grimp branch
assumed unknown-module queries return empty (the AST fallback's contract), but grimp 3.15 raises
`ModuleNotPresent` — so `test_atlas` failed with 5 errors in every grimp-installed environment
(CI never sees it: grimp is dev-only and CI installs runtime deps only — a CI-invisible failure
class). Reproduced on pristine main via a worktree (pre-existing, not this PR's regression);
root-fixed by guarding both `importers()`/`downstream()` with an in-graph check so the two engines
share one total-function contract. 22 atlas/context_map tests green; full mirror green after.

**⚑ Self-initiated:** the stale-claim removal; the A/B's concrete protocol fills (seed project
design, task corpus, judge blinding posture — all within companion D's frame); the G2
"fail → fix → re-run" recommended ruling (flagged for the owner at G1, not silently adopted).
Everything else was the owner's in-chat direction.

## 💡 Session idea (Q-0089)

**Make `adopt` render-what-it-knows** — captured not as a separate idea file but as the G2
report §3(2) remainder (it is now *the* next substrate-kit work item, evidence-backed): adopt
should run the kit's existing render machinery over the facts it can detect (project name from
the dir, verify command from pyproject/CI), and stamp every remaining placeholder with a loud
"UNRENDERED — run `bootstrap ask`" banner instead of silent `${...}`. Why it's worth having: the
A/B measured the silent-template failure mode costing real orientation words in every session
shape; this converts the kit's worst cold-start liability into its front door.

## ⟲ Previous-session review (Q-0102)

The previous session (#1770, the consolidation) set this one up unusually well — the canonical
plan's §5 steps 1–3 were executable verbatim, and companion D's procedure held up in contact with
reality with only declared deltas (fresh-context ≈ fresh-container, N=1/pair). What it missed:
companion D specified *measuring* the kit but never asked "what does the ON arm actually SEE at
minute zero?" — a 30-second manual `adopt` + `ls && head` smoke of the arm would have caught the
unrendered-template state before spending 8 sessions. **Workflow improvement:** any A/B or eval
procedure should include a "walk one arm manually first" smoke step before the paired runs — the
experiment's biggest finding was discoverable in its setup phase.

## Documentation audit (Q-0104)

`check_docs --strict` ✓ (after the orphan-homing catch — the briefing + report are both linked
from `docs/planning/README.md`) · `check_current_state_ledger.py --strict` ✓ (benign lag only) ·
`check_amendments` ✓ (local + live CI) · full CI mirror (`check_quality.py --full`) run before the
card flip — result recorded in the final commit. Decisions homed: the G2 verdict + ruling live in
the report + canonical plan (not chat-only); the S3 sector ▶ points at the remainder. New owner
decisions: none made (the G2 ruling is decided-and-flagged for G1 per Q-0240). Claim file deleted
at close.
