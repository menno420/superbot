# Session — Hermes research deepening (context-management root cause, verified vs. source)

> **Status:** `in-progress` — born-red per Q-0133. Owner asked for "more research" on why the
> Hermes control-plane agent misbehaves (errors, forgotten tasks, misunderstood assignments,
> not syncing to main); he supplied a ChatGPT deep-research report on the Nous Research Hermes
> Agent. About to: verify that report against Hermes source/docs, map it onto SuperBot's actual
> setup, correct the in-repo token-efficiency investigation, and fix one concrete SOUL.md bug.

## What I'm about to do
- Extend `docs/operations/hermes-token-efficiency-investigation-2026-06-15.md` with verified
  findings: the real root cause is **compaction** (tool-output pruning at 50% + the 400-msg
  gateway-hygiene valve, #12626), not unbounded growth; the exact `compression.*` config knobs;
  cron's stateless+pre-run-`script` model as the bounded-dispatch implementation; SOUL.md
  truncation risk; upstream issues to watch (#12626, #9763).
- Fix the SOUL.md operating-prompt sync bug: `git fetch origin main` alone leaves a STALE working
  tree, so Hermes reads old files even after "syncing" → the owner's "forgets to sync to main".
