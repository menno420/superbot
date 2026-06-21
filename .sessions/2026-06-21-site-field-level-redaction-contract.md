# 2026-06-21 — site.json field-level redaction contract

> **Status:** `in-progress` — tooling/test/docs only (no `disbot/` runtime changed) → self-merge on
> green (Q-0113).

> **Run type:** routine · dispatch

## What I'm about to do

Scheduled dispatch, no work order → advance the plan. Current-state ▶ Next ungated startable lists
the last ungated stdlib-guard candidate `public-data-contract-field-snapshot` (idea
`docs/ideas/public-data-contract-field-snapshot-2026-06-19.md`). Building it: extend the public
`site.json` redaction guard from the **family** boundary (`SITE_TOPLEVEL_KEYS`) down to the **leaf
field** boundary, so a producer change that adds a new field to an already-allowed family fails
closed instead of leaking silently. Clean, contained, stdlib, self-mergeable.
