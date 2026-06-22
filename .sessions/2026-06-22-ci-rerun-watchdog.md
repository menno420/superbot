# 2026-06-22 — CI dropped-`synchronize` auto-re-trigger watchdog

> **Status:** `in-progress` — owner-endorsed follow-up to the Q-0195 session. Builds the captured
> idea (`docs/ideas/ci-dropped-synchronize-auto-retrigger-2026-06-22.md`): a scheduled watchdog that
> re-kicks `code-quality` when a `claude/*` PR head has **no** run — the *silent* CI stall (GitHub
> drops the `pull_request: synchronize` event → no run → no failure webhook → auto-merge waits
> forever). Owner-directed in-session ("Yes go ahead") → merge on green; no `needs-hermes-review`.

> **Run type:** `manual · owner-directed`

## Why

PR #1283 sat blocked because GitHub dropped the `synchronize` event and `code-quality` never ran on
the head. The cancellation race was already fixed (#1275, `cancel-in-progress: false`); this is the
*distinct* dropped-delivery failure mode. Manual remedy was an empty commit — this automates it.

## What shipped

_(filled in as the work lands; flipped to `complete` as the final step)_

## ⟲ Previous-session review

_(end-of-session)_

## 💡 Session idea

_(end-of-session)_
