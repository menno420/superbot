# 2026-06-30 — AI review-log backlog triage, round 1 (DDT confabulation)

> **Status:** `in-progress`
<!-- born-red flow (Q-0133): `in-progress` while open; flipped to `complete` as the final close step. -->

**Branch:** `claude/ai-answer-storage-plan-3fvdit` (restarted from main; PR #1569 merged)
**Run type:** manual (owner-directed) — follow-up to the #1569 answer-loop, on a real export

## What I'm about to do

The owner ran `!aireview export` (the command shipped in #1569) and pasted the 6-entry backlog.
Triaged it with `scripts/ai_review_triage.py` + per-entry verification (`btd6_probe.py`):

- **Entries 1 & 2 (DDT counters):** the *real* issue. Grounding is **correct** (the
  `[btd6_interaction]` fact even says "recommend by rules, don't auto-list towers" + flags the
  Ice/Glue MOAB-class exceptions), but **haiku-4.5 confabulated wrong specific towers past it**
  (Ice 2-0-0 / Ace 0-2-5 / Sniper 0-4-0 — the exact #1492 errors). A model-faithfulness gap, not
  a data gap; the DDT grounding is already pinned by `btd6_corpus.py:120`.
- **Entries 3, 4, 5 (Bloonarius/Monkey-Meadow optimization + fragments):** the bot **correctly**
  declined an unsolvable global-optimization ask and asked for clarification on context-less
  follow-ups. Working as intended — not bugs.
- **Entry 6 (T5 Bloonarius track time):** a genuine **data gap** — track lengths aren't in the
  dump, so the bot's "I don't have that" is honest.

This is a **docs-only** capture PR: record the production-confirmed DDT-confabulation finding +
the **vetted rules-based DDT answer** (the source text for a preset / future deterministic answer)
in the BTD6 QA corpus, so the deferred "tower recommendations" task has concrete material. The
actual per-question fix is an **owner-authored preset** (drafted for the owner in chat) — preset
rows live in prod, which this session can't write.
