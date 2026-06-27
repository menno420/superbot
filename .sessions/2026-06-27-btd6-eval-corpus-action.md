# 2026-06-27 — BTD6 QA corpus wired into the evals (offline grounding test + live action suite)

> **Status:** `complete`

**Run type:** owner-directed (follow-up to PR #1487)

## What this run did

Owner asked: *"update the evals action so I can test all these questions at once — would that be
trustworthy? does the evals have access to the stored data?"* Honest finding: the eval **harness probes
the model with hand-canned `tool_results` + a generic system prompt — it does NOT touch
`btd6_context_service.build()`**, so naively dumping the corpus in would test the model in a vacuum, not
the bot's retrieval. Made it trustworthy by keying both new layers off the bot's REAL grounding.

**PR — BTD6 QA-accuracy corpus in the eval system.**

1. **`tests/evals/btd6_corpus.py`** — the machine-readable corpus (`GROUNDING_PROBES`): each question +
   the answer-bearing fact its real grounding must contain (`expect`) and the known wrong claim it must
   not (`forbid`). One source feeding both layers.
2. **`tests/evals/test_btd6_qa_corpus.py`** — the **offline, deterministic, creds-free** layer: runs each
   question through the real `build()` and asserts the fact is grounded. Runs every PR. This is the
   trustworthy "all at once" check — it proves the stored data is accessible + correct per question with
   no model variance.
3. **`scripts/run_evals.py --btd6`** + **`.github/workflows/ai-evals.yml` `suite:` picker** — the
   **live, paid** layer: builds one `EvalCase` per question whose system prompt is the question's real
   `build()` facts, then grades the model's phrased answer. Because the grounding is the bot's own, a
   pass means "with the facts our bot actually retrieves, the model answers right" — not "answers from
   perfect hand-fed context."
4. Docs: `tests/evals/README.md` + the corpus doc explain the offline-vs-live trust split.

CI: `check_quality --check-only` green; the offline corpus test + the eval harness/coverage tests pass
(34) with no API keys.

## ⚑ Self-initiated

None unprompted — owner-directed ("update the evals action"). The offline grounding layer is the
trustworthy implementation of "test all these questions at once."

## 💡 Session idea (Q-0089)

*Promote `test_btd6_qa_corpus.py` into a tiny reusable `grounding_probe` fixture other knowledge domains
reuse (Project Moon already has the same build()/guard shape).* The offline "does the real pipeline
ground the answer-bearing fact?" pattern is domain-agnostic; a shared probe helper would let the next
knowledge domain get an accuracy corpus for free. Routed as an idea (Project Moon's corpus would be the
first reuse), not built here.

## ⟲ Previous-session review (Q-0102)

The immediately-prior work (PR #1487, this session's first half) shipped the interaction grounding +
corpus but left the corpus as a **human-readable doc only** — the owner's very next question ("can I test
these at once?") shows a doc isn't enough; a corpus wants a machine half wired into CI. Good that #1487's
corpus doc was structured enough to lift directly into `GROUNDING_PROBES`. **Workflow improvement
(applied):** an accuracy corpus should ship with its offline probe test in the same arc, so "verified
once" becomes "verified every PR" without a follow-up ask.

## 🧾 Doc audit (Q-0104)

`check_docs`/`check_consistency` green. New facts homed: the eval trust-model in `tests/evals/README.md`
+ the testing section in the corpus doc. No new owner decision to route. Ledger: this PR is added by the
next reconciliation pass (merged-only convention).
