# 2026-06-30 — AI review-log answer loop (export → triage → presets)

> **Status:** `in-progress`

## What I'm about to do

Close the feedback loop on the AI answer review-log (#1494). Today the bot *records*
the questions it got wrong / didn't know (`ai_review_log`), but nothing turns that
backlog back into correct answers, and the rows are only viewable via `!aireview list`
in Discord.

Owner decisions this session (AskUserQuestion, 2026-06-30):
- **Answer mechanism = Both** — root-cause fixes + regression evals *and* a runtime
  vetted-answer preset layer.
- **Getting the backlog = build `!aireview export`, then paste** — the rows live in
  prod Postgres which the sandbox can't read, so the owner exports and pastes them.

Building (sequenced so the export ships first and unblocks the owner's paste):

- **PR 1 (this card):** `!aireview export` (full backlog → JSON/text, read-only) +
  `scripts/ai_review_triage.py` (group/dedupe/scaffold probes — generalizes the BTD6
  corpus loop) + a backlog runbook.
- **PR 2:** the `ai_answer_presets` table + audited service + a `natural_language_stage`
  short-circuit (serve a vetted answer with zero API, byte-identical when empty) +
  `!aireview preset …` operator commands.
- **PR 3 (gated on the owner's export paste):** per-question root-cause fixes / presets,
  each pinned with a regression probe, then `!aireview resolve`.
