# 2026-06-27 — BTD6 evals: faithful "exactly live" answer-path replay

> **Status:** `complete`

**Run type:** owner-directed (follow-up to PR #1488)

## What this run did

Owner wanted the eval action to give *"exactly the results that a live test would give."* PR #1488's
live layer injected the real grounding into a simplified prompt (good, but not the live system prompt or
the faithfulness guard). This run closes that gap: a faithful replay of the **real production answer
path**, reusing production internals so there's no approximation and minimal drift.

**PR — `tests/evals/btd6_live_path.py`.**

- `run_live(question)` replays one question through the SAME components the live
  `AINaturalLanguageStage` uses, in the same order: real `ai_task_router.classify` → real
  `btd6_context_service.build` grounding → real `ai_instruction_service.assemble` instruction stack →
  real `natural_language_stage._invoke_gateway` (tools, orchestration, round-cash workflow, ledger) →
  real `validate_btd6_reply` guard + `_build_grounding_constraint` regenerate-once → real
  `_btd6_no_data_refusal`. Pre-model deterministic floors are checked too. **Zero production code
  change** — it reuses the internals, which is what keeps it from drifting.
- `run_btd6_live_suite()` + `render_live_report()` grade every corpus probe's final live reply.
- `scripts/run_evals.py --btd6` / `--btd6-only` run it; the *AI Evals* action **suite: btd6** maps to
  `--btd6-only` and points `AI_DEFAULT_PROVIDER` at the chosen provider (the one the live path tests).
- Replaced #1488's approximation (`live_cases`) with this; the **offline** grounding test
  (`test_btd6_qa_corpus.py`) is unchanged + gained a wiring guard that runs `run_live` offline (degrades,
  never raises) on every PR.

Why faithful + safe: `_invoke_gateway` is DB-safe (it degrades the DB-backed bits and, with no key,
returns a deterministic non-answer), so the path runs in CI; with a real key it produces the genuine
live reply. Verified offline: the whole path executes without raising; the only non-reproduced parts are
Discord I/O + the audit log, neither of which changes the answer text.

CI: `check_quality --check-only` green; all 140 `tests/evals/` pass with no API keys.

## ⚑ Self-initiated

None unprompted — owner asked for exactly-live fidelity. Chose the reuse-internals replay over a
hot-path refactor specifically to avoid touching the bot's riskiest code while still being faithful.

## 💡 Session idea (Q-0089)

*Add a `--diff` mode to the live suite that prints, per probe, the grounded facts vs the model's reply
side by side.* When a live BTD6 answer fails, the fastest triage is "did the fact ground, and did the
model use it?" — the replay already has both in hand. Routed as an idea, not built (keeps this PR
focused on the faithful path itself).

## ⟲ Previous-session review (Q-0102)

PR #1488 was right to ship the offline layer first (it's the trustworthy core) but shipped a live layer
I *described* to the owner as an approximation — and the very next ask was "make it exactly live." Lesson
applied this run: when the deliverable is "test like production," reach for **reusing the production
seam** first, not a parallel re-implementation — the reuse is both more faithful and less code. The one
residual is drift risk (the replay mirrors `process`'s order); mitigated with a cross-reference note +
the offline wiring guard, but a future shared-seam extraction in `natural_language_stage` would remove it
entirely (noted, not done — it touches the hot path).

## 🧾 Doc audit (Q-0104)

`check_docs`/`check_consistency` green. Homed: the faithful-path explanation in `tests/evals/README.md`
+ the corpus doc testing section (both updated from "approximation" to "real production path"). No new
owner decision to route. Ledger: added by the next reconciliation pass (merged-only convention).
