# 2026-06-30 — AI review-log backlog triage, round 1 (DDT confabulation)

> **Status:** `complete`
<!-- born-red flow (Q-0133): `in-progress` while open; flipped to `complete` as the final close step. -->

**PR:** [#1572](https://github.com/menno420/superbot/pull/1572) — BTD6 corpus: prod DDT-confabulation finding.
**Branch:** `claude/ai-answer-storage-plan-3fvdit` (restarted from main; PR #1569 merged).
**Run type:** manual (owner-directed) — follow-up to the #1569 answer-loop, on a real export.

## What this run did

The owner ran `!aireview export` (the command shipped in #1569) and pasted the 6-entry backlog —
the answer loop's first real round-trip. Triaged it with `scripts/ai_review_triage.py` + per-entry
verification (`btd6_probe.py`):

- **Entries 1 & 2 (DDT counters):** the *real* issue. Grounding is **correct** (the
  `[btd6_interaction]` fact even says "recommend by rules, don't auto-list towers" + flags the
  Ice/Glue MOAB-class exceptions), but **haiku-4.5 confabulated wrong specific towers past it**
  (Ice 2-0-0 / Ace 0-2-5 / Sniper 0-4-0 — the exact #1492 errors). A **model-faithfulness gap**,
  not a data gap; the DDT grounding is already pinned by `btd6_corpus.py:120`.
- **Entries 3, 4, 5 (Bloonarius/Monkey-Meadow optimization + fragments):** the bot **correctly**
  declined an unsolvable global-optimization ask and asked for clarification on context-less
  follow-ups. Working as intended — not bugs.
- **Entry 6 (T5 Bloonarius track time):** a genuine **data gap** — track lengths aren't in the
  dump, so the bot's "I don't have that" is honest.

## Shipped (PR #1572, docs-only)

Recorded in `docs/btd6/qa-accuracy-corpus-2026-06-27.md`: a **Production review-log finding**
section (the confabulation, production-confirming the #1492 concern), the mitigation ladder
(vetted preset → stronger model → deterministic floor), and the **verified rules-based DDT answer**
— the source text for the owner's preset / a future deterministic floor. The deferred tower-rec
follow-up now cross-references it.

The actual per-question fix is an **owner-authored preset** (drafted in chat) — preset rows live in
prod, which an agent session can't write. No code change: the grounding is correct + tested, and a
guard change to catch confabulated tower builds is exactly the #1492 over-refusal trap.

## Decisions made alone (owner should be aware)

- **No code fix shipped.** The honest finding is that 5/6 entries are the bot behaving well and the
  6th is a model-faithfulness issue best handled by an owner-vetted preset (the #1569 mechanism) —
  not a contained code bug. I chose a docs-capture + an owner preset draft over a risky guard change.
- The vetted DDT answer is **rules-based, no specific tower build codes** (respects the owner-deferred
  tower-recommendation decision; the verified content is straight from the committed interaction data).

## 💡 Session idea (Q-0089)

**Resolve-*with-reason* on the review log.** This session showed the triage script's coarse spot:
4 of 6 `grounding_failed` entries were the bot **working correctly** (honest refusals / a real data
gap), not gaps to fix — but the log can only mark them generically `reviewed`. Add a small
disposition vocabulary at resolve time — `fixed` / `presetted` / `working-as-intended` /
`wont-fix-data-gap` — stored on `ai_review_log` and shown in `!aireview list` / export. Then a
re-export skips the settled "the bot was actually right" entries and the backlog converges instead
of re-surfacing honest refusals every round. Distinct from the frequency-suggestions idea filed last
session (that ranks *what to fix*; this records *the outcome*). Dedup-checked `docs/ideas/`.

## ⟲ Previous-session review (Q-0102)

Previous = the answer-loop build (#1569, this branch's first PR). **Did well:** shipped a complete,
well-tested loop (export → triage → presets) end-to-end + a friction→guard, and the export command
worked first try on real prod data. **Missed / improvement:** the triage script classifies purely by
`reason_code` (everything `grounding_failed` → `fix`), which this real export proved is too coarse —
it labeled 4 honest-refusal/data-gap entries `fix`. The concrete improvement is the Q-0089 idea above
(resolve-with-reason), so the loop distinguishes "the bot was right" from "needs work" instead of
leaning on a human to re-judge every round. The loop *worked*; using it once revealed the next sharpening.

## 🛠 Friction → guard

No new enforcing-guard-worthy friction this run (it was analysis on a docs-only change; the
force-with-lease push is the expected merged-branch-restart flow, not friction). The one real insight
— the triage over-classifies honest refusals — is a *feature* gap captured as the Q-0089 idea, not a
guard. Per the Q-0089/Q-0102 honesty bar, not inventing a guard where there isn't one.

## ⚑ Self-initiated

Owner-directed task (the owner pasted the export → "work the backlog"). The **docs-capture scope** is
my judgment call on how to work it, given the per-question fix is an owner-action preset and there's
no contained code bug — flagging it here for visibility, not an unprompted idea→plan promotion.

## Doc audit (Q-0104)

`check_quality --check-only` green (docs reachable, artifacts fresh). Finding + vetted answer captured
in the corpus (durable home), not left in chat. No new owner *rules* / router changes. Did not touch
`current-state.md` Recently-shipped (merged-PRs-only; next session reconciles).
