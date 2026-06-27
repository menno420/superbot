# 2026-06-27 — AI answer review-log (didn't-know + user corrections)

> **Status:** `in-progress` — born-red card; flips to `complete` as the final step.

## What this session is about

Owner request: *"anytime the AI does not know an answer properly, or gets corrected
by a user, log the question and its answer someplace we can review it."*

Two owner design calls (AskUserQuestion, 2026-06-27):
- **Correction detection** = react **and** reply (a 👎 on the bot's answer, or a reply
  to it that reads as a correction).
- **Review surface** = dedicated review channel **and** a queryable log.

## Plan (in progress)

- New `ai_review_log` table (migration 100) — captures the redacted question + answer
  for (a) every "didn't-know" outcome and (b) every user correction.
- `services/ai_review_log_service.py` — single chokepoint (record_unknown /
  record_correction / query / mark_reviewed), in-memory answer registry for
  correction-matching, emits `ai.review_logged`.
- `cogs/ai_review_cog.py` — 👎-reaction + correction-reply listeners, the
  `ai.review_logged` → review-channel poster, and the `!aireview` staff command group.
- `natural_language_stage.py` — best-effort `record_unknown` at the three "didn't-know"
  audit seams + `remember_answer` after a reply is sent.

_(Arc / shipped / findings / Context delta / enders filled in at close.)_
